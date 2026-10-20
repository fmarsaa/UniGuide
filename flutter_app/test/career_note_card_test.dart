import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:uniguide_mobile/models/student_profile.dart';
import 'package:uniguide_mobile/widgets/career_note_card.dart';

Future<void> _show(WidgetTester tester, CareerNoteLoader loader) async {
  await tester.pumpWidget(MaterialApp(
    home: Scaffold(body: SingleChildScrollView(child: CareerNoteCard(profile: StudentProfile(), loader: loader))),
  ));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('the card names the programme and the grade that is short', (tester) async {
    await _show(tester, (_) async => [
          {
            'career': 'Medical Doctor (Physician/Surgeon)',
            'programme': 'Bachelor of Medicine and Bachelor of Surgery (MBChB)',
            'reasons': ['English: asks for at least B, and your grade is D+'],
          }
        ]);
    expect(find.text('About the career you picked'), findsOneWidget);
    expect(find.text('Bachelor of Medicine and Bachelor of Surgery (MBChB)'), findsOneWidget);
    expect(find.textContaining('your grade is D+'), findsOneWidget);
  });

  testWidgets('nothing is shown when no programme is being held back', (tester) async {
    await _show(tester, (_) async => []);
    expect(find.text('About the career you picked'), findsNothing);
  });
}
