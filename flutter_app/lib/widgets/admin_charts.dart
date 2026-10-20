import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

const Color kChartTeal = Color(0xFF0EA5A4);
const Color kChartIndigo = Color(0xFF6366F1);
const Color kChartAmber = Color(0xFFF59E0B);
const Color kChartRed = Color(0xFFEF4444);

/// A titled card that holds one chart or list on the admin Insights page.
class ChartCard extends StatelessWidget {
  final String title;
  final String? note;
  final Widget child;

  const ChartCard({Key? key, required this.title, this.note, required this.child}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.cardBackground(context),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.cardBorder(context)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context))),
          if (note != null) ...[
            const SizedBox(height: 2),
            Text(note!, style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context))),
          ],
          const SizedBox(height: 14),
          child,
        ],
      ),
    );
  }
}

/// Shown instead of a chart when there is nothing to draw yet.
class EmptyChartMessage extends StatelessWidget {
  final String message;
  const EmptyChartMessage(this.message, {Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) => SizedBox(
        height: 90,
        child: Center(
          child: Text(message, textAlign: TextAlign.center, style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context))),
        ),
      );
}

/// One headline number with a label.
class KpiTile extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const KpiTile({Key? key, required this.label, required this.value, required this.icon, required this.color}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.cardBackground(context),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.cardBorder(context)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: color),
          const SizedBox(height: 8),
          Text(value, style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context))),
          const SizedBox(height: 2),
          Text(label, style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context))),
        ],
      ),
    );
  }
}

double _niceInterval(double maxY) => maxY <= 6 ? 1 : (maxY / 4).ceilToDouble();

FlTitlesData _titles(BuildContext context, {required double maxY, required String Function(int) bottomLabel, int every = 1}) {
  final style = TextStyle(fontSize: 9, color: AppColors.textSecondary(context));
  return FlTitlesData(
    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
    leftTitles: AxisTitles(
      sideTitles: SideTitles(
        showTitles: true,
        reservedSize: 28,
        interval: _niceInterval(maxY),
        getTitlesWidget: (value, meta) => Text(value.toInt().toString(), style: style),
      ),
    ),
    bottomTitles: AxisTitles(
      sideTitles: SideTitles(
        showTitles: true,
        reservedSize: 22,
        interval: 1,
        getTitlesWidget: (value, meta) {
          final i = value.toInt();
          if (i % every != 0) return const SizedBox.shrink();
          return Padding(padding: const EdgeInsets.only(top: 4), child: Text(bottomLabel(i), style: style));
        },
      ),
    ),
  );
}

FlGridData _grid(BuildContext context, double maxY) => FlGridData(
      show: true,
      drawVerticalLine: false,
      horizontalInterval: _niceInterval(maxY),
      getDrawingHorizontalLine: (_) => FlLine(color: AppColors.cardBorder(context), strokeWidth: 1),
    );

/// A bar for each label (a day, a grade band or a star rating).
class BarSeriesChart extends StatelessWidget {
  final List<String> labels;
  final List<double> values;
  final Color color;
  final int labelEvery;
  final double height;

  const BarSeriesChart({
    Key? key,
    required this.labels,
    required this.values,
    this.color = kChartTeal,
    this.labelEvery = 1,
    this.height = 180,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (values.isEmpty || values.every((v) => v == 0)) return const EmptyChartMessage('Nothing to show yet.');
    final maxY = (values.reduce((a, b) => a > b ? a : b) + 1).clamp(2.0, double.infinity);
    final barWidth = values.length > 20 ? 5.0 : 16.0;
    return SizedBox(
      height: height,
      child: BarChart(
        BarChartData(
          maxY: maxY,
          alignment: BarChartAlignment.spaceBetween,
          gridData: _grid(context, maxY),
          borderData: FlBorderData(show: false),
          titlesData: _titles(context, maxY: maxY, every: labelEvery, bottomLabel: (i) => i >= 0 && i < labels.length ? labels[i] : ''),
          barGroups: [
            for (int i = 0; i < values.length; i++)
              BarChartGroupData(x: i, barRods: [
                BarChartRodData(toY: values[i], width: barWidth, color: color, borderRadius: const BorderRadius.vertical(top: Radius.circular(2))),
              ]),
          ],
        ),
      ),
    );
  }
}

/// A line that rises or falls over time, for example the running number of students.
class TrendLineChart extends StatelessWidget {
  final List<String> labels;
  final List<double> values;
  final Color color;
  final int labelEvery;

  const TrendLineChart({Key? key, required this.labels, required this.values, this.color = kChartIndigo, this.labelEvery = 7}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (values.isEmpty || values.last == 0) return const EmptyChartMessage('No students have registered yet.');
    final maxY = (values.reduce((a, b) => a > b ? a : b) + 1).clamp(2.0, double.infinity);
    return SizedBox(
      height: 180,
      child: LineChart(
        LineChartData(
          minY: 0,
          maxY: maxY,
          gridData: _grid(context, maxY),
          borderData: FlBorderData(show: false),
          titlesData: _titles(context, maxY: maxY, every: labelEvery, bottomLabel: (i) => i >= 0 && i < labels.length ? labels[i] : ''),
          lineBarsData: [
            LineChartBarData(
              spots: [for (int i = 0; i < values.length; i++) FlSpot(i.toDouble(), values[i])],
              isCurved: false,
              color: color,
              barWidth: 2.5,
              dotData: const FlDotData(show: false),
              belowBarData: BarAreaData(show: true, color: color.withOpacity(0.12)),
            ),
          ],
        ),
      ),
    );
  }
}

class DonutSlice {
  final String label;
  final int value;
  final Color color;
  const DonutSlice(this.label, this.value, this.color);
}

/// Parts of a whole, with a legend that gives each count and share.
class DonutChart extends StatelessWidget {
  final List<DonutSlice> slices;
  const DonutChart({Key? key, required this.slices}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final total = slices.fold<int>(0, (sum, s) => sum + s.value);
    if (total == 0) return const EmptyChartMessage('Nothing to show yet.');
    return Row(
      children: [
        SizedBox(
          width: 130,
          height: 130,
          child: PieChart(
            PieChartData(
              sectionsSpace: 2,
              centerSpaceRadius: 34,
              sections: [
                for (final s in slices)
                  if (s.value > 0) PieChartSectionData(value: s.value.toDouble(), color: s.color, radius: 22, showTitle: false),
              ],
            ),
          ),
        ),
        const SizedBox(width: 18),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final s in slices)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    children: [
                      Container(width: 10, height: 10, decoration: BoxDecoration(color: s.color, borderRadius: BorderRadius.circular(2))),
                      const SizedBox(width: 8),
                      Expanded(child: Text(s.label, style: TextStyle(fontSize: 12, color: AppColors.textPrimary(context)))),
                      Text('${s.value} (${(100 * s.value / total).round()}%)',
                          style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context))),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

/// Horizontal bars that show how many students reach each step, each as a share of the first.
class FunnelBars extends StatelessWidget {
  final List<MapEntry<String, int>> steps;
  const FunnelBars({Key? key, required this.steps}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final first = steps.isEmpty ? 0 : steps.first.value;
    if (first == 0) return const EmptyChartMessage('No students have registered yet.');
    return Column(
      children: [
        for (final step in steps)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 5),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(child: Text(step.key, style: TextStyle(fontSize: 12, color: AppColors.textPrimary(context)))),
                    Text('${step.value}  (${(100 * step.value / first).round()}%)',
                        style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context))),
                  ],
                ),
                const SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: step.value / first,
                    minHeight: 8,
                    backgroundColor: AppColors.chipBackground(context),
                    valueColor: const AlwaysStoppedAnimation<Color>(kChartTeal),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}

/// A short ranked list: a name and a count on each line.
class RankedList extends StatelessWidget {
  final List<MapEntry<String, int>> items;
  final String emptyMessage;
  const RankedList({Key? key, required this.items, required this.emptyMessage}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return EmptyChartMessage(emptyMessage);
    return Column(
      children: [
        for (int i = 0; i < items.length; i++)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 5),
            child: Row(
              children: [
                SizedBox(width: 22, child: Text('${i + 1}.', style: TextStyle(fontSize: 12, color: AppColors.textSecondary(context)))),
                Expanded(child: Text(items[i].key, style: TextStyle(fontSize: 12, color: AppColors.textPrimary(context)))),
                Text('${items[i].value}', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textPrimary(context))),
              ],
            ),
          ),
      ],
    );
  }
}
