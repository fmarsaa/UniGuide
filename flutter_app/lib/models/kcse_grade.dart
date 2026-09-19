enum KCSEGrade {
  a(12, 'A'),
  aMinus(11, 'A-'),
  bPlus(10, 'B+'),
  b(9, 'B'),
  bMinus(8, 'B-'),
  cPlus(7, 'C+'),
  c(6, 'C'),
  cMinus(5, 'C-'),
  dPlus(4, 'D+'),
  d(3, 'D'),
  dMinus(2, 'D-'),
  e(1, 'E');

  final int points;
  final String label;

  const KCSEGrade(this.points, this.label);

  static KCSEGrade fromString(String str) {
    return KCSEGrade.values.firstWhere(
      (g) => g.label.toUpperCase() == str.toUpperCase(),
      orElse: () => KCSEGrade.cPlus,
    );
  }
}
