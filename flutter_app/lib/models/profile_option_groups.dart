/// Display-only grouping of the profile-setup options.
///
/// The app is for students who have NOT decided on a career, so headings are
/// deliberately about what a student enjoys doing ("Numbers, data & computers")
/// and never about professions or fields ("Health", "Law", "Engineering"),
/// which would nudge an undecided student toward a career before they have
/// chosen one. Career aspirations are shown as one flat list (no headings).
///
/// The option strings themselves are what the trained Random Forest knows
/// (kept in exact sync with backend/synthetic_data_generator.py), so they are
/// never renamed here - this file only decides which heading each one sits
/// under. Anything not listed falls into an "Other" group at runtime (see
/// `withOtherGroup`), so a newly added option can never silently disappear
/// from the screen.
library;

const String kThemePeople = 'Helping & caring for people';
const String kThemeNumbers = 'Numbers, data & computers';
const String kThemeBuilding = 'Building, making & fixing things';
const String kThemeScience = 'Science & discovery';
const String kThemeNature = 'Nature, food & the environment';
const String kThemeIdeas = 'Words, ideas & society';
const String kThemeBusiness = 'Business, money & organising';

const Map<String, List<String>> kInterestGroups = {
  kThemePeople: [
    'Healthcare & Clinical Medicine',
    'Patient Care & Nursing',
    'Dental & Oral Health Care',
    'Physical Rehabilitation & Therapy',
    'Public Health & Epidemiology',
    'Counseling & Mental Health Support',
    'Social Research & Community Development',
    'Veterinary & Animal Health Care',
  ],
  kThemeNumbers: [
    'Software Development & Coding',
    'Artificial Intelligence & Machine Learning',
    'Data Analytics & Statistics',
    'Cybersecurity & Network Defense',
    'Mathematical Research & Data Science',
    'Actuarial Modeling & Risk Analysis',
    'Business Systems & Enterprise Technology',
  ],
  kThemeBuilding: [
    'Civil Infrastructure & Structural Engineering',
    'Electrical & Electronic Systems',
    'Robotics, Mechatronics & Automation',
    'Mechanical Systems & Manufacturing',
    'Architecture & Building Design',
    'Urban Planning & Land Use',
    'Geospatial Mapping & Remote Sensing',
  ],
  kThemeScience: [
    'Pharmaceutical Sciences',
    'Clinical Laboratory & Diagnostic Sciences',
    'Chemical & Materials Sciences',
    'Physics & Applied Sciences Research',
    'Food Science & Nutrition',
  ],
  kThemeNature: [
    'Agribusiness & Food Sustainability',
    'Food Production & Agro-Processing',
    'Environmental Conservation & Sustainability',
  ],
  kThemeIdeas: [
    'Journalism & Media Production',
    'Corporate Law & Constitutional Advocacy',
    'Teaching & Curriculum Development',
    'Political & Governance Studies',
    'Criminal Justice & Security Studies',
    'Economic Policy & Market Analysis',
  ],
  kThemeBusiness: [
    'Financial Markets & Investment Banking',
    'Human Resource & Organizational Development',
    'International Trade & Global Business',
    'Procurement & Supply Chain Management',
    'General Business Administration & Strategy',
    'Tourism & Destination Management',
    'Hospitality & Guest Services',
  ],
};

const String kSkillPeople = 'Working with people';
const String kSkillNumbers = 'Numbers, data & computers';
const String kSkillDesign = 'Designing, building & mapping';
const String kSkillLab = 'Lab & field science';
const String kSkillIdeas = 'Writing, debating & analysing society';
const String kSkillTrade = 'Trade, planning & negotiating';
const String kSkillGeneral = 'General';

const Map<String, List<String>> kSkillGroups = {
  kSkillPeople: [
    'Clinical Diagnostics & Health Care',
    'Patient Assessment & Rehabilitation Technique',
    'Epidemiological Surveillance & Health Education',
    'Pedagogy & Classroom Management',
    'Social Research Methods & Community Engagement',
    'Case Management & Counseling Ethics',
    'Active Listening & Psychological Assessment',
    'Guest Relations & Hospitality Service Standards',
    'Recruitment & Employee Relations',
  ],
  kSkillNumbers: [
    'Python & Software Programming',
    'Mathematical & Quantitative Analysis',
    'Statistical Modeling & Programming (R/Python)',
    'Problem Solving & Analytical Logic',
    'Financial Modeling & Accounting',
  ],
  kSkillDesign: [
    'CAD Modeling & Spatial Engineering',
    'Cost Estimation & Construction Economics',
    'Land Use Planning & GIS Mapping',
    'GIS Software & Remote Sensing',
    'Property Valuation & Market Analysis',
    'Medical Device Design & Signal Processing',
  ],
  kSkillLab: [
    'Scientific Laboratory Research',
    'Chemical Analysis & Process Optimization',
    'Microbial Culturing & Laboratory Research',
    'Agricultural & Environmental Science',
    'Forest Resource Assessment & Conservation Planning',
    'Environmental Monitoring & Impact Assessment',
  ],
  kSkillIdeas: [
    'Critical Thinking & Persuasive Debate',
    'News Writing & Media Research',
    'Political Analysis & Policy Research',
    'Criminal Justice Analysis & Investigation',
  ],
  kSkillTrade: [
    'Cross-Cultural Trade & Market Entry Strategy',
    'Supply Chain Analysis & Contract Negotiation',
    'Destination Marketing & Itinerary Planning',
  ],
  kSkillGeneral: [
    'Attention to Detail',
    'Team Collaboration & Leadership',
  ],
};

/// Group names that always stay at the bottom, whatever the shuffle does.
const Set<String> kPinnedLastGroups = {kSkillGeneral, 'Other'};

/// Returns [groups] plus an "Other" group holding every option in [all] that
/// no group lists, so grouping can never hide a real option.
Map<String, List<String>> withOtherGroup(Map<String, List<String>> groups, List<String> all) {
  final known = groups.values.expand((g) => g).toSet();
  final other = all.where((o) => !known.contains(o)).toList();
  return {...groups, if (other.isNotEmpty) 'Other': other};
}
