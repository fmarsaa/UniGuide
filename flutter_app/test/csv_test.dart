import 'package:flutter_test/flutter_test.dart';
import 'package:uniguide_mobile/utils/csv.dart';

void main() {
  test('every cell is quoted so commas never split a row', () {
    final csv = toCsv(['Name', 'Comment'], [
      ['Amina', 'Great app, very clear'],
    ]);
    expect(csv, '"Name","Comment"\r\n"Amina","Great app, very clear"');
  });

  test('quotes inside a cell are doubled', () {
    final csv = toCsv(['Comment'], [
      ['She said "good"'],
    ]);
    expect(csv.split('\r\n')[1], '"She said ""good"""');
  });

  test('line breaks inside a cell stay inside that cell', () {
    final csv = toCsv(['Details'], [
      ['line one\nline two'],
    ]);
    expect(csv, '"Details"\r\n"line one\nline two"');
  });

  test('missing values become empty cells', () {
    expect(toCsv(['A', 'B'], [
      [null, 3],
    ]), '"A","B"\r\n"","3"');
  });
}
