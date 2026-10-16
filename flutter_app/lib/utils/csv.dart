/// Builds CSV text. Every cell is quoted, and quotes inside a cell are doubled, so
/// commas, quotes and line breaks in comments or details can never break a row.
String toCsv(List<String> header, List<List<Object?>> rows) {
  String cell(Object? value) =>
      '"${(value ?? '').toString().replaceAll('"', '""')}"';
  final lines = <String>[header.map(cell).join(',')];
  for (final row in rows) {
    lines.add(row.map(cell).join(','));
  }
  return lines.join('\r\n');
}
