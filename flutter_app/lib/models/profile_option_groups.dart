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

const Set<String> kPinnedLastGroups = {'Other'};

/// Returns [groups] plus an "Other" group holding every option in [all] that
/// no group lists, so grouping can never hide a real option.
Map<String, List<String>> withOtherGroup(Map<String, List<String>> groups, List<String> all) {
  final known = groups.values.expand((g) => g).toSet();
  final other = all.where((o) => !known.contains(o)).toList();
  return {...groups, if (other.isNotEmpty) 'Other': other};
}
