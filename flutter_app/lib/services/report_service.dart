import 'dart:typed_data';

import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';

import '../models/recommendation.dart';
import '../models/student_profile.dart';

/// Builds "My UniGuide report": the student's results and top programmes as a PDF
/// they can keep, print, or take to a parent or career counsellor. Every figure is
/// copied from the recommendation the student already saw - nothing is recalculated.
class ReportService {
  ReportService._();

  /// Opens the phone's share sheet (or downloads, in a browser) with the report.
  static Future<void> shareReport(
      StudentProfile profile, List<RecommendationItem> recommendations) async {
    final bytes = await buildReport(profile, recommendations);
    await Printing.sharePdf(bytes: bytes, filename: 'UniGuide-report.pdf');
  }

  static Future<Uint8List> buildReport(
      StudentProfile profile, List<RecommendationItem> recommendations) async {
    final doc = pw.Document(title: 'My UniGuide report', author: 'UniGuide');
    final today = DateTime.now();
    final date =
        '${today.day.toString().padLeft(2, '0')}/${today.month.toString().padLeft(2, '0')}/${today.year}';

    const teal = PdfColor.fromInt(0xFF0EA5A4);
    const navy = PdfColor.fromInt(0xFF14213D);
    const grey = PdfColor.fromInt(0xFF64748B);

    pw.Widget heading(String text) => pw.Padding(
          padding: const pw.EdgeInsets.only(top: 16, bottom: 6),
          child: pw.Text(_safe(text),
              style: pw.TextStyle(
                  fontSize: 14, fontWeight: pw.FontWeight.bold, color: navy)),
        );
    pw.Widget small(String text,
            {bool bold = false, PdfColor color = PdfColors.black}) =>
        pw.Text(
          _safe(text),
          style: pw.TextStyle(
              fontSize: 10,
              color: color,
              fontWeight: bold ? pw.FontWeight.bold : pw.FontWeight.normal),
        );

    final grades = profile.grades.entries.toList()
      ..sort((a, b) => a.key.compareTo(b.key));
    final name = profile.fullName.trim().isEmpty ? '' : profile.fullName.trim();

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(36),
        footer: (ctx) => pw.Padding(
          padding: const pw.EdgeInsets.only(top: 10),
          child: pw.Text(
            'Page ${ctx.pageNumber} of ${ctx.pagesCount}',
            style: const pw.TextStyle(fontSize: 8, color: grey),
          ),
        ),
        build: (ctx) => [
          pw.Text('UniGuide',
              style: pw.TextStyle(
                  fontSize: 24, fontWeight: pw.FontWeight.bold, color: teal)),
          pw.Text('My programme report',
              style: pw.TextStyle(fontSize: 14, color: navy)),
          pw.SizedBox(height: 4),
          small('Prepared on $date${name.isEmpty ? '' : ' for $name'}',
              color: grey),
          pw.Divider(color: PdfColors.grey400),
          heading('Your KCSE results'),
          if (grades.isEmpty)
            small('No grades were entered.')
          else
            pw.Wrap(
              spacing: 18,
              runSpacing: 4,
              children: [for (final g in grades) small('${g.key}: ${g.value}')],
            ),
          pw.SizedBox(height: 4),
          small('Mean grade: ${profile.kcseMeanGrade}', bold: true),
          heading('Your top programme matches'),
          for (final rec in recommendations) ...[
            pw.Container(
              margin: const pw.EdgeInsets.only(bottom: 12),
              padding: const pw.EdgeInsets.all(10),
              decoration: pw.BoxDecoration(
                border: pw.Border.all(color: PdfColors.grey400),
                borderRadius: pw.BorderRadius.circular(6),
              ),
              child: pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  pw.Text(
                    _safe('${rec.rank}. ${rec.programme.title}'),
                    style: pw.TextStyle(
                        fontSize: 12, fontWeight: pw.FontWeight.bold),
                  ),
                  small('${rec.programme.code}  |  ${rec.programme.faculty}',
                      color: grey),
                  pw.SizedBox(height: 4),
                  small(
                    rec.meetsMinimumRequirements
                        ? 'Entry check: ${rec.eligibilityStatus}'
                        : 'Entry check: ${rec.eligibilityStatus} (not a qualifying match - shown as the closest option)',
                    bold: true,
                  ),
                  small(
                      'Latest cutoff points: ${rec.programme.cutoffRangeLabel}'),
                  if (rec.programme.minimumSubjectRequirements.isNotEmpty)
                    small(
                      'Minimum subject grades: ${rec.programme.minimumSubjectRequirements.entries.map((e) => '${e.key} ${e.value}').join(', ')}',
                    ),
                  if (rec.plainReasons.isNotEmpty) ...[
                    pw.SizedBox(height: 4),
                    small('Why it was suggested:', bold: true),
                    for (final reason in rec.plainReasons) small('- $reason'),
                  ],
                  if (rec.programme.offeringUniversities.isNotEmpty) ...[
                    pw.SizedBox(height: 4),
                    small('Universities offering it (latest cutoff points):',
                        bold: true),
                    for (final u in rec.programme.offeringUniversities)
                      small(
                        u.latestCutoff > 0
                            ? '- ${u.universityName}: ${u.latestCutoff.toStringAsFixed(1)}'
                            : '- ${u.universityName}',
                      ),
                  ],
                ],
              ),
            ),
          ],
          pw.SizedBox(height: 6),
          pw.Divider(color: PdfColors.grey400),
          pw.Text(
            'Cutoff points are the latest published by KUCCPS and change every year. Meeting a cutoff does not guarantee a place. '
            'Always confirm the requirements and the current cutoffs at kuccps.net before you apply.',
            style: const pw.TextStyle(fontSize: 8, color: grey),
          ),
        ],
      ),
    );

    return doc.save();
  }

  /// The PDF's built-in font only covers basic Latin characters, so swap common
  /// typographic characters for plain ones and drop anything else it cannot draw.
  static String _safe(String text) {
    const swaps = {
      '–': '-',
      '—': '-',
      '‘': "'",
      '’': "'",
      '“': '"',
      '”': '"',
      '•': '-'
    };
    final buffer = StringBuffer();
    for (final rune in text.runes) {
      final ch = String.fromCharCode(rune);
      if (swaps.containsKey(ch)) {
        buffer.write(swaps[ch]);
      } else if (rune < 256) {
        buffer.write(ch);
      }
    }
    return buffer.toString();
  }
}
