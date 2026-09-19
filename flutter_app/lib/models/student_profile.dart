import 'kcse_grade.dart';

class StudentProfile {
  final String uid;
  final String fullName;
  final String indexNumber;
  final String kcseMeanGrade;
  final int kcseMeanPoints;
  final Map<String, String> grades; // e.g. {"Mathematics": "A", "English": "B+"}
  final List<String> interests;
  final List<String> skills;
  final List<String> strengths;
  final List<String> aspirations;
  final double calculatedClusterScore;
  final DateTime updatedAt;

  StudentProfile({
    String? uid,
    String? id,
    this.fullName = 'Candidate Profile',
    this.indexNumber = '',
    this.kcseMeanGrade = 'B',
    int? kcseMeanPoints,
    Map<String, String>? grades,
    List<String>? interests,
    List<String>? skills,
    List<String>? strengths,
    List<String>? aspirations,
    this.calculatedClusterScore = 0.0,
    DateTime? updatedAt,
  })  : uid = uid ?? id ?? 'cand_default',
        kcseMeanPoints = kcseMeanPoints ?? KCSEGrade.fromString(kcseMeanGrade ?? 'B').points,
        grades = grades ?? {},
        interests = interests ?? [],
        skills = skills ?? [],
        strengths = strengths ?? [],
        aspirations = aspirations ?? [],
        updatedAt = updatedAt ?? DateTime.now();

  String get id => uid;

  factory StudentProfile.fromJson(Map<String, dynamic> json) {
    return StudentProfile(
      uid: json['uid'] ?? json['id'] ?? '',
      fullName: json['fullName'] ?? '',
      indexNumber: json['indexNumber'] ?? '',
      kcseMeanGrade: json['kcseMeanGrade'] ?? 'B',
      kcseMeanPoints: json['kcseMeanPoints'] ?? 9,
      grades: Map<String, String>.from(json['grades'] ?? {}),
      interests: List<String>.from(json['interests'] ?? []),
      skills: List<String>.from(json['skills'] ?? []),
      strengths: List<String>.from(json['strengths'] ?? []),
      aspirations: List<String>.from(json['aspirations'] ?? []),
      calculatedClusterScore: (json['calculatedClusterScore'] as num?)?.toDouble() ?? 0.0,
      updatedAt: json['updatedAt'] != null
          ? DateTime.parse(json['updatedAt'])
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() => {
    'uid': uid,
    'id': uid,
    'fullName': fullName,
    'indexNumber': indexNumber,
    'kcseMeanGrade': kcseMeanGrade,
    'kcseMeanPoints': kcseMeanPoints,
    'grades': grades,
    'interests': interests,
    'skills': skills,
    'strengths': strengths,
    'aspirations': aspirations,
    'calculatedClusterScore': calculatedClusterScore,
    'updatedAt': updatedAt.toIso8601String(),
  };
}
