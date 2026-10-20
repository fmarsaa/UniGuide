import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uniguide_mobile/widgets/admin_charts.dart';

Future<void> _show(WidgetTester tester, Widget child) async {
  await tester.binding.setSurfaceSize(const Size(420, 900));
  await tester.pumpWidget(MaterialApp(home: Scaffold(body: SingleChildScrollView(child: child))));
}

void main() {
  testWidgets('a bar chart with no counts says there is nothing to show instead of an empty axis', (tester) async {
    await _show(tester, const BarSeriesChart(labels: ['A', 'B'], values: [0, 0]));
    expect(find.text('Nothing to show yet.'), findsOneWidget);
  });

  testWidgets('a bar chart with counts draws without an error', (tester) async {
    await _show(tester, const BarSeriesChart(labels: ['A', 'B', 'C'], values: [1, 4, 2]));
    expect(find.text('Nothing to show yet.'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('the registration line says so when nobody has registered', (tester) async {
    await _show(tester, const TrendLineChart(labels: ['10-01', '10-02'], values: [0, 0]));
    expect(find.text('No students have registered yet.'), findsOneWidget);
  });

  testWidgets('a donut chart lists each part with its count and share', (tester) async {
    await _show(tester, const DonutChart(slices: [
      DonutSlice('Named a career', 3, kChartTeal),
      DonutSlice('Not sure yet', 1, kChartAmber),
    ]));
    expect(find.text('3 (75%)'), findsOneWidget);
    expect(find.text('1 (25%)'), findsOneWidget);
  });

  testWidgets('the journey bars give each step as a share of the students registered', (tester) async {
    await _show(tester, const FunnelBars(steps: [
      MapEntry('Registered', 4),
      MapEntry('Received recommendations', 3),
    ]));
    expect(find.text('4  (100%)'), findsOneWidget);
    expect(find.text('3  (75%)'), findsOneWidget);
  });

  testWidgets('the journey bars show a message when nobody has registered', (tester) async {
    await _show(tester, const FunnelBars(steps: [MapEntry('Registered', 0)]));
    expect(find.text('No students have registered yet.'), findsOneWidget);
  });

  testWidgets('a ranked list with nothing in it shows the given message', (tester) async {
    await _show(tester, const RankedList(items: [], emptyMessage: 'No programmes have been saved yet.'));
    expect(find.text('No programmes have been saved yet.'), findsOneWidget);
  });
}
