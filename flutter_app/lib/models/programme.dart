class UniversityOffering {
  final String universityName;
  final String universityType; // Public or Private
  final String location;
  final double latestCutoff;
  final double previousCutoff;
  final String kuccpsCode;

  UniversityOffering({
    required this.universityName,
    required this.universityType,
    required this.location,
    required this.latestCutoff,
    required this.previousCutoff,
    required this.kuccpsCode,
  });

  factory UniversityOffering.fromJson(Map<String, dynamic> json) {
    return UniversityOffering(
      universityName: json['universityName'] ?? '',
      universityType: json['universityType'] ?? 'Public',
      location: json['location'] ?? 'Kenya',
      latestCutoff: (json['latestCutoff'] as num?)?.toDouble() ?? 0.0,
      previousCutoff: (json['previousCutoff'] as num?)?.toDouble() ?? 0.0,
      kuccpsCode: json['kuccpsCode'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
    'universityName': universityName,
    'universityType': universityType,
    'location': location,
    'latestCutoff': latestCutoff,
    'previousCutoff': previousCutoff,
    'kuccpsCode': kuccpsCode,
  };
}

class Programme {
  final String id;
  final String code;
  final String title;
  final String faculty;
  final String minMeanGrade;
  final double averageCutoff;
  final String clusterGroup;
  final List<String> clusterSubjects;
  final Map<String, String> minimumSubjectRequirements;
  final String description;
  final List<String> careerOpportunities;
  final List<String> requiredSkills;
  final List<String> professionalCertifications;
  final List<UniversityOffering> offeringUniversities;
  final int durationYears;

  Programme({
    required this.id,
    required this.code,
    required this.title,
    required this.faculty,
    required this.minMeanGrade,
    required this.averageCutoff,
    required this.clusterGroup,
    required this.clusterSubjects,
    required this.minimumSubjectRequirements,
    required this.description,
    required this.careerOpportunities,
    required this.requiredSkills,
    required this.professionalCertifications,
    required this.offeringUniversities,
    this.durationYears = 4,
  });

  factory Programme.fromJson(Map<String, dynamic> json) {
    return Programme(
      id: json['id'] ?? '',
      code: json['code'] ?? '',
      title: json['title'] ?? '',
      faculty: json['faculty'] ?? '',
      minMeanGrade: json['minMeanGrade'] ?? 'C+',
      averageCutoff: (json['averageCutoff'] as num?)?.toDouble() ?? 0.0,
      clusterGroup: json['clusterGroup'] ?? '',
      clusterSubjects: List<String>.from(json['clusterSubjects'] ?? []),
      minimumSubjectRequirements: Map<String, String>.from(json['minimumSubjectRequirements'] ?? {}),
      description: json['description'] ?? '',
      careerOpportunities: List<String>.from(json['careerOpportunities'] ?? []),
      requiredSkills: List<String>.from(json['requiredSkills'] ?? []),
      professionalCertifications: List<String>.from(json['professionalCertifications'] ?? []),
      offeringUniversities: (json['offeringUniversities'] as List? ?? [])
          .map((u) => UniversityOffering.fromJson(u))
          .toList(),
      durationYears: json['durationYears'] ?? 4,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'code': code,
    'title': title,
    'faculty': faculty,
    'minMeanGrade': minMeanGrade,
    'averageCutoff': averageCutoff,
    'clusterGroup': clusterGroup,
    'clusterSubjects': clusterSubjects,
    'minimumSubjectRequirements': minimumSubjectRequirements,
    'description': description,
    'careerOpportunities': careerOpportunities,
    'requiredSkills': requiredSkills,
    'professionalCertifications': professionalCertifications,
    'offeringUniversities': offeringUniversities.map((u) => u.toJson()).toList(),
    'durationYears': durationYears,
  };
}
