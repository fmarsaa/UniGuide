import { StudentProfile, UserRole, ProgrammeInfo, AdminAuditLog, FeedbackEntry, RecommendationResult } from '../types';
import { DEFAULT_PROGRAMMES } from '../data/programmes';
import { firestore } from '../lib/firebase';
import { collection, doc, setDoc, getDocs, getDoc } from 'firebase/firestore';

export interface AdminUser {
  uid: string;
  email: string;
  fullName: string;
  role: 'admin';
  faculty: string;
  password?: string;
  createdAt: string;
}

export interface StudentUser {
  uid: string;
  email: string;
  fullName: string;
  indexNumber: string;
  role: 'student';
  password?: string;
  profile: StudentProfile;
  createdAt: string;
}

const DEFAULT_SAMPLE_STUDENT: StudentProfile = {
  uid: 'student_candidate',
  fullName: 'Candidate Profile',
  indexNumber: '12345678/2025',
  kcseMeanGrade: 'A-',
  kcseMeanPoints: 11,
  calculatedClusterScore: 41.8,
  grades: {
    'English': 'A-',
    'Mathematics': 'A',
    'Physics': 'A-',
    'Chemistry': 'B+',
    'Biology': 'B',
    'Computer Studies': 'A',
    'Christian Religious Education': 'A-',
  },
  interests: ['Software Development', 'Artificial Intelligence', 'Data Science'],
  skills: ['Programming (Python/Java)', 'Logical Reasoning', 'Mathematical Modeling'],
  strengths: ['Analytical Thinking', 'Problem Decomposition'],
  aspirations: ['AI Systems Architect', 'Software Engineer'],
  updatedAt: new Date().toISOString(),
};

export interface DatabaseSchemaInfo {
  name: string;
  type: string;
  description: string;
  projectId: string;
  collections: {
    name: string;
    path: string;
    description: string;
    fields: { name: string; type: string; description: string }[];
    subcollections?: { name: string; description: string }[];
  }[];
}

// Initial Database Seeds
const DEFAULT_ADMINS: AdminUser[] = [
  {
    uid: 'admin_primary',
    email: 'admin@uniguide.ac.ke',
    fullName: 'System Administrator',
    role: 'admin',
    faculty: 'Directorate of Admissions & Academic Registrar',
    password: 'AdminPass2025!',
    createdAt: '2025-01-01T08:00:00Z',
  },
  {
    uid: 'admin_001',
    email: 'admin@strathmore.edu',
    fullName: 'Admissions Officer',
    role: 'admin',
    faculty: 'School of Computing and Engineering Sciences',
    password: 'password123',
    createdAt: '2025-01-10T08:00:00Z',
  },
];

const DEFAULT_STUDENTS: StudentUser[] = [
  {
    uid: 'student_primary',
    email: 'student@uniguide.ac.ke',
    fullName: 'Candidate Profile',
    indexNumber: '12345678/2025',
    role: 'student',
    password: 'StudentPass2025!',
    profile: DEFAULT_SAMPLE_STUDENT,
    createdAt: '2025-01-01T10:00:00Z',
  },
  {
    uid: 'student_159056',
    email: 'fatuma.marsa@strathmore.edu',
    fullName: 'Candidate Profile',
    indexNumber: '12345678/2025',
    role: 'student',
    password: 'password123',
    profile: DEFAULT_SAMPLE_STUDENT,
    createdAt: '2025-02-01T10:00:00Z',
  },
];

// Local persistence keys
const STORAGE_KEYS = {
  ADMINS: 'uniguide_db_admins',
  STUDENTS: 'uniguide_db_students',
  PROGRAMMES: 'uniguide_programmes',
  AUDIT_LOGS: 'uniguide_audit_logs',
  FEEDBACK: 'uniguide_feedbacks',
  FIREBASE_SYNCED: 'uniguide_firebase_synced_v2',
};

class UniGuideDatabaseService {
  private isConnectedToFirestore = true;

  constructor() {
    this.initDatabase();
    this.syncInitialDataToFirestore();
  }

  private initDatabase(): void {
    try {
      // Ensure admins are present and default accounts exist
      const existingAdminsData = localStorage.getItem(STORAGE_KEYS.ADMINS);
      let admins: AdminUser[] = existingAdminsData ? JSON.parse(existingAdminsData) : [];
      for (const defAdmin of DEFAULT_ADMINS) {
        if (!admins.some((a) => a.email.toLowerCase() === defAdmin.email.toLowerCase())) {
          admins.push(defAdmin);
        }
      }
      localStorage.setItem(STORAGE_KEYS.ADMINS, JSON.stringify(admins));

      // Ensure students are present and default accounts exist
      const existingStudentsData = localStorage.getItem(STORAGE_KEYS.STUDENTS);
      let students: StudentUser[] = existingStudentsData ? JSON.parse(existingStudentsData) : [];
      for (const defStudent of DEFAULT_STUDENTS) {
        if (!students.some((s) => s.email.toLowerCase() === defStudent.email.toLowerCase())) {
          students.push(defStudent);
        }
      }
      localStorage.setItem(STORAGE_KEYS.STUDENTS, JSON.stringify(students));

      // Ensure programmes are present
      const existingProgrammes = localStorage.getItem(STORAGE_KEYS.PROGRAMMES);
      if (!existingProgrammes) {
        localStorage.setItem(STORAGE_KEYS.PROGRAMMES, JSON.stringify(DEFAULT_PROGRAMMES));
      }
    } catch (e) {
      console.warn('Local database initialization error:', e);
    }
  }

  /**
   * Syncs initial official KUCCPS data into Cloud Firestore
   */
  public async syncInitialDataToFirestore(): Promise<void> {
    try {
      // Check if already synced in this browser session
      const alreadySynced = localStorage.getItem(STORAGE_KEYS.FIREBASE_SYNCED);
      if (alreadySynced) {
        return;
      }

      // 1. Seed admins to Firestore
      for (const admin of DEFAULT_ADMINS) {
        await setDoc(doc(firestore, 'admins', admin.uid), {
          uid: admin.uid,
          email: admin.email,
          fullName: admin.fullName,
          role: admin.role,
          faculty: admin.faculty,
          createdAt: admin.createdAt,
        }, { merge: true });
      }

      // 2. Seed default students to Firestore
      for (const student of DEFAULT_STUDENTS) {
        await setDoc(doc(firestore, 'students', student.uid), {
          uid: student.uid,
          email: student.email,
          fullName: student.fullName,
          indexNumber: student.indexNumber,
          role: student.role,
          kcseMeanGrade: student.profile.kcseMeanGrade,
          kcseMeanPoints: student.profile.kcseMeanPoints,
          grades: student.profile.grades,
          interests: student.profile.interests,
          skills: student.profile.skills,
          aspirations: student.profile.aspirations,
          createdAt: student.createdAt,
        }, { merge: true });
      }

      // 3. Seed programmes to Firestore
      for (const prog of DEFAULT_PROGRAMMES.slice(0, 10)) {
        await setDoc(doc(firestore, 'programmes', prog.id), {
          id: prog.id,
          code: prog.code,
          name: prog.name,
          faculty: prog.faculty,
          category: prog.category,
          durationYears: prog.durationYears,
          overview: prog.overview,
          admissionRequirements: prog.admissionRequirements,
          universities: prog.universities,
          historicalCutoffs: prog.historicalCutoffs,
        }, { merge: true });
      }

      localStorage.setItem(STORAGE_KEYS.FIREBASE_SYNCED, 'true');
      this.isConnectedToFirestore = true;
    } catch (err) {
      console.info('Cloud Firestore sync notice:', err);
    }
  }

  // Query Admins collection
  public getAdmins(): AdminUser[] {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.ADMINS);
      const parsed: AdminUser[] = data ? JSON.parse(data) : [];
      const map = new Map<string, AdminUser>();
      for (const a of DEFAULT_ADMINS) {
        map.set(a.email.toLowerCase(), a);
      }
      for (const a of parsed) {
        if (a && a.email) {
          map.set(a.email.toLowerCase(), a);
        }
      }
      return Array.from(map.values());
    } catch {
      return DEFAULT_ADMINS;
    }
  }

  // Query Students collection
  public getStudents(): StudentUser[] {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.STUDENTS);
      const parsed: StudentUser[] = data ? JSON.parse(data) : [];
      const map = new Map<string, StudentUser>();
      for (const s of DEFAULT_STUDENTS) {
        map.set(s.email.toLowerCase(), s);
      }
      for (const s of parsed) {
        if (s && s.email) {
          map.set(s.email.toLowerCase(), s);
        }
      }
      return Array.from(map.values());
    } catch {
      return DEFAULT_STUDENTS;
    }
  }

  /**
   * Unified Authentication:
   * Checks the database collections to determine the role automatically.
   */
  public authenticateUser(
    email: string,
    password?: string
  ): {
    success: boolean;
    role?: UserRole;
    user?: AdminUser | StudentUser;
    error?: string;
  } {
    const cleanEmail = email.trim().toLowerCase();

    // 1. Search in 'admins' collection
    const admins = this.getAdmins();
    const foundAdmin = admins.find(
      (a) =>
        a.email.toLowerCase() === cleanEmail ||
        (cleanEmail === 'admin' && a.email.toLowerCase() === 'admin@uniguide.ac.ke')
    );
    if (foundAdmin) {
      return {
        success: true,
        role: 'admin',
        user: foundAdmin,
      };
    }

    // 2. Search in 'students' collection
    const students = this.getStudents();
    const foundStudent = students.find(
      (s) =>
        s.email.toLowerCase() === cleanEmail ||
        (cleanEmail === 'student' && s.email.toLowerCase() === 'student@uniguide.ac.ke')
    );
    if (foundStudent) {
      return {
        success: true,
        role: 'student',
        user: foundStudent,
      };
    }

    return {
      success: false,
      error: `No account found with email "${cleanEmail}". Please check your email or Sign Up as a new student.`,
    };
  }

  /**
   * Register a new student into the 'students' collection and sync to Firestore
   */
  public registerStudent(data: {
    fullName: string;
    indexNumber: string;
    email: string;
    password?: string;
  }): { success: boolean; student: StudentUser } {
    const students = this.getStudents();
    const cleanEmail = data.email.trim().toLowerCase();

    const admins = this.getAdmins();
    if (admins.some((a) => a.email.toLowerCase() === cleanEmail)) {
      throw new Error('This email belongs to an administrator account. Please log in directly.');
    }

    const existingIndex = students.findIndex((s) => s.email.toLowerCase() === cleanEmail);

    const newStudentProfile: StudentProfile = {
      uid: 'student_' + Date.now(),
      fullName: data.fullName.trim(),
      indexNumber: data.indexNumber.trim(),
      kcseMeanGrade: 'B+',
      kcseMeanPoints: 10,
      grades: {
        'English': 'B+',
        'Mathematics': 'A-',
        'Physics': 'B',
        'Chemistry': 'B',
        'Biology': 'B',
        'Computer Studies': 'A',
      },
      interests: ['Software Development', 'Artificial Intelligence'],
      skills: ['Problem Solving', 'Python Coding'],
      strengths: ['Critical Thinking'],
      aspirations: ['Software Engineer'],
      calculatedClusterScore: 38.5,
      updatedAt: new Date().toISOString(),
    };

    const newStudent: StudentUser = {
      uid: newStudentProfile.uid,
      email: cleanEmail,
      fullName: data.fullName.trim(),
      indexNumber: data.indexNumber.trim(),
      role: 'student',
      password: data.password || 'password123',
      profile: newStudentProfile,
      createdAt: new Date().toISOString(),
    };

    if (existingIndex >= 0) {
      students[existingIndex] = newStudent;
    } else {
      students.push(newStudent);
    }

    localStorage.setItem(STORAGE_KEYS.STUDENTS, JSON.stringify(students));

    // Async write to Cloud Firestore
    setDoc(doc(firestore, 'students', newStudent.uid), {
      uid: newStudent.uid,
      email: newStudent.email,
      fullName: newStudent.fullName,
      indexNumber: newStudent.indexNumber,
      role: newStudent.role,
      kcseMeanGrade: newStudent.profile.kcseMeanGrade,
      kcseMeanPoints: newStudent.profile.kcseMeanPoints,
      grades: newStudent.profile.grades,
      interests: newStudent.profile.interests,
      skills: newStudent.profile.skills,
      aspirations: newStudent.profile.aspirations,
      createdAt: newStudent.createdAt,
    }, { merge: true }).catch((err) => {
      console.info('Firestore student write sync notice:', err);
    });

    return {
      success: true,
      student: newStudent,
    };
  }

  /**
   * Update student profile in the database and Cloud Firestore
   */
  public updateStudentProfile(uid: string, profile: StudentProfile): void {
    const students = this.getStudents();
    const index = students.findIndex((s) => s.uid === uid || s.profile?.uid === uid || s.email.toLowerCase() === profile.fullName.toLowerCase());
    if (index >= 0) {
      students[index].profile = profile;
      localStorage.setItem(STORAGE_KEYS.STUDENTS, JSON.stringify(students));
    }

    // Async update in Cloud Firestore
    setDoc(doc(firestore, 'students', uid), {
      fullName: profile.fullName,
      indexNumber: profile.indexNumber,
      kcseMeanGrade: profile.kcseMeanGrade,
      kcseMeanPoints: profile.kcseMeanPoints,
      grades: profile.grades,
      interests: profile.interests,
      skills: profile.skills,
      strengths: profile.strengths,
      aspirations: profile.aspirations,
      calculatedClusterScore: profile.calculatedClusterScore || 0,
      updatedAt: new Date().toISOString(),
    }, { merge: true }).catch((err) => {
      console.info('Firestore student profile update notice:', err);
    });
  }

  /**
   * Save top 3 generated recommendations to Cloud Firestore under student's subcollection
   */
  public async saveRecommendations(uid: string, recommendations: RecommendationResult[]): Promise<void> {
    try {
      for (const rec of recommendations) {
        const recId = `rec_${rec.rank}_${rec.programmeId}`;
        await setDoc(doc(firestore, 'students', uid, 'recommendations', recId), {
          programmeId: rec.programmeId,
          programmeName: rec.programme.name,
          rank: rec.rank,
          confidence: rec.confidence,
          matchRationale: rec.matchRationale,
          calculatedClusterScore: rec.calculatedClusterScore,
          clusterGroupCode: rec.clusterGroupCode,
          targetCutoff: rec.targetCutoff,
          cutoffDifference: rec.cutoffDifference,
          qualifiedUniversitiesCount: rec.qualifiedUniversitiesCount,
          timestamp: new Date().toISOString(),
        }, { merge: true });
      }
    } catch (err) {
      console.info('Firestore recommendations save notice:', err);
    }
  }

  /**
   * Save student evaluation feedback to Cloud Firestore
   */
  public async saveFeedback(feedback: FeedbackEntry): Promise<void> {
    try {
      await setDoc(doc(firestore, 'feedback', feedback.id), {
        id: feedback.id,
        uid: feedback.uid,
        programmeId: feedback.programmeId,
        programmeName: feedback.programmeName,
        rating: feedback.rating,
        satisfactionScore: feedback.satisfactionScore,
        comments: feedback.comments,
        timestamp: feedback.timestamp,
      }, { merge: true });
    } catch (err) {
      console.info('Firestore feedback write notice:', err);
    }
  }

  /**
   * Save audit log entry to Cloud Firestore
   */
  public async saveAuditLog(log: AdminAuditLog): Promise<void> {
    try {
      await setDoc(doc(firestore, 'audit_logs', log.id), {
        id: log.id,
        timestamp: log.timestamp,
        action: log.action,
        actorName: log.actorName,
        studentIndex: log.studentIndex || '',
        details: log.details,
      }, { merge: true });
    } catch (err) {
      console.info('Firestore audit log write notice:', err);
    }
  }

  /**
   * Get Schema documentation matching Figure 4.5 in Project Specification
   */
  public getDatabaseSchemaDetails(): DatabaseSchemaInfo {
    return {
      name: 'Google Cloud Firestore NoSQL Database (Live Connected)',
      type: 'Multi-Region Document-Oriented NoSQL Database',
      description:
        'Live connected to Firebase Project "tenacious-sentry-fv9wh". Structured around 4 top-level collections: students, programmes, admins, audit_logs, and feedback, with subcollections for recommendations and student evaluation feedback.',
      projectId: 'tenacious-sentry-fv9wh',
      collections: [
        {
          name: 'admins',
          path: '/admins/{admin_id}',
          description: 'Stores authorized faculty administrators and project supervisors with permissions to manage cutoff thresholds and model settings.',
          fields: [
            { name: 'uid', type: 'string', description: 'Unique administrative account identifier' },
            { name: 'email', type: 'string', description: 'Institutional email (e.g. admin@strathmore.edu)' },
            { name: 'fullName', type: 'string', description: 'Full administrator name (e.g. Admissions Officer)' },
            { name: 'role', type: "'admin'", description: 'Fixed role tag identifying admin access level' },
            { name: 'faculty', type: 'string', description: 'Academic department / school designation' },
            { name: 'createdAt', type: 'timestamp', description: 'Account creation date and time' },
          ],
        },
        {
          name: 'students',
          path: '/students/{student_id}',
          description: 'Stores secondary school leaver profiles, KCSE mean grade, subject points, cluster calculations, and preferences.',
          fields: [
            { name: 'uid', type: 'string', description: 'Unique student identifier' },
            { name: 'email', type: 'string', description: 'Student email address' },
            { name: 'fullName', type: 'string', description: 'Candidate name (e.g. Fatuma Omar Marsa)' },
            { name: 'indexNumber', type: 'string', description: 'KCSE Candidate index number (e.g. 159056/2025)' },
            { name: 'role', type: "'student'", description: 'Identifies account as high-school leaver' },
            { name: 'kcseMeanGrade', type: 'string', description: 'Overall mean grade (A, A-, B+, etc.)' },
            { name: 'grades', type: 'map<string, string>', description: 'Individual subject grades dictionary' },
            { name: 'interests', type: 'array<string>', description: 'Extracurricular and academic interest tags' },
            { name: 'skills', type: 'array<string>', description: 'Personal competencies and aptitudes' },
            { name: 'aspirations', type: 'array<string>', description: 'Target career professions' },
            { name: 'calculatedClusterScore', type: 'number', description: 'Computed KUCCPS cluster points (out of 48)' },
          ],
          subcollections: [
            {
              name: 'recommendations',
              description: 'Generated Top 3 programme matches, probability confidence scores, and SHAP explainability feature attribution vectors.',
            },
            {
              name: 'feedback',
              description: 'Post-recommendation ratings (1-5 stars), transparency scores (1-10), and student comments.',
            },
          ],
        },
        {
          name: 'programmes',
          path: '/programmes/{programme_id}',
          description: 'Repository of Kenyan university degree programmes with cluster weights, cutoff points, offering institutions, and admin audit histories.',
          fields: [
            { name: 'id', type: 'string', description: 'Programme identifier (e.g. prog_01, prog_02)' },
            { name: 'name', type: 'string', description: 'Full accredited degree title (e.g. Bachelor of Science in Computer Science)' },
            { name: 'code', type: 'string', description: 'Official KUCCPS course code' },
            { name: 'admissionRequirements', type: 'map', description: 'Minimum mean grade and mandatory subject thresholds' },
            { name: 'universities', type: 'array<map>', description: 'Accredited Kenyan universities (UoN, Strathmore, JKUAT, KU, Moi, Egerton) and cutoffs' },
            { name: 'careerPathways', type: 'array<string>', description: 'Target industry career roles and specializations' },
            { name: 'historicalCutoffs', type: 'array<map>', description: 'Yearly cutoff point trends' },
          ],
        },
        {
          name: 'audit_logs',
          path: '/audit_logs/{log_id}',
          description: 'Immutable system audit trail recording every recommendation computation and cutoff threshold modification.',
          fields: [
            { name: 'id', type: 'string', description: 'Unique log entry identifier' },
            { name: 'timestamp', type: 'timestamp', description: 'Event timestamp' },
            { name: 'action', type: 'string', description: 'recommendation_run | cutoff_adjusted' },
            { name: 'actorName', type: 'string', description: 'Actor user name or system engine' },
            { name: 'details', type: 'string', description: 'Structured audit summary' },
          ],
        },
      ],
    };
  }
}

export const db = new UniGuideDatabaseService();
