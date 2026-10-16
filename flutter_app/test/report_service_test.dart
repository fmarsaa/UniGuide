import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:uniguide_mobile/models/programme.dart';
import 'package:uniguide_mobile/models/recommendation.dart';
import 'package:uniguide_mobile/models/student_profile.dart';
import 'package:uniguide_mobile/services/report_service.dart';

Programme _programme({String title = 'Bachelor of Science in Nursing'}) => Programme(
      id: 'prog_nursing',
      code: 'NUR-103',
      title: title,
      faculty: 'School of Nursing',
      minMeanGrade: 'B',
      averageCutoff: 43.0,
      clusterGroup: 'Cluster 1',
      clusterSubjects: ['Biology', 'Chemistry', 'Mathematics', 'English'],
      minimumSubjectRequirements: {'Chemistry': 'C+', 'Biology': 'C+'},
      description: 'Nursing.',
      careerOpportunities: ['Nurse'],
      requiredSkills: ['Empathy'],
      professionalCertifications: [],
      offeringUniversities: [
        UniversityOffering(
          universityName: 'University of Nairobi',
          universityType: 'Public',
          location: 'Nairobi',
          latestCutoff: 43.676,
          previousCutoff: 43.297,
          kuccpsCode: '1263132',
        ),
      ],
      durationYears: 4,
    );

RecommendationItem _recommendation(Programme programme) => RecommendationItem(
      rank: 1,
      programme: programme,
      confidenceScore: 0.5,
      studentClusterScore: 44.0,
      cutoffDiff: 0.3,
      eligibilityStatus: 'Meets the latest cutoff',
      meetsMinimumRequirements: true,
      shapExplanations: const [],
      primaryReason: 'Primarily driven by interests.',
      plainReasons: const ['You said you are interested in Patient Care & Nursing.'],
    );

void main() {
  final profile = StudentProfile(
    fullName: 'Amina Test',
    kcseMeanGrade: 'B+',
    grades: {'Mathematics': 'B+', 'Chemistry': 'A-'},
  );

  test('the report is a real PDF file', () async {
    final bytes = await ReportService.buildReport(profile, [_recommendation(_programme())]);
    expect(latin1.decode(bytes.sublist(0, 5)), '%PDF-');
    expect(bytes.length, greaterThan(1500));
  });

  test('a programme name with characters the PDF font cannot draw does not break the report', () async {
    final bytes = await ReportService.buildReport(
      profile,
      [_recommendation(_programme(title: 'Bachelor of Commerce – Finance • Accounting \u{1F393}'))],
    );
    expect(latin1.decode(bytes.sublist(0, 5)), '%PDF-');
  });

  test('a report can be built with no recommendations or grades', () async {
    final bytes = await ReportService.buildReport(StudentProfile(), const []);
    expect(latin1.decode(bytes.sublist(0, 5)), '%PDF-');
  });
}
