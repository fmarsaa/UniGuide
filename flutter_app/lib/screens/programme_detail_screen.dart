import 'package:flutter/material.dart';
import '../models/programme.dart';

class ProgrammeDetailScreen extends StatelessWidget {
  final Programme programme;

  const ProgrammeDetailScreen({Key? key, required this.programme}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: Text(programme.code, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF14213D),
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Title Header Card
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey.shade200),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.03),
                    blurRadius: 10,
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0EA5A4).withOpacity(0.12),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      programme.faculty,
                      style: const TextStyle(color: Color(0xFF0EA5A4), fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    programme.title,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      _buildMetricChip(Icons.calendar_today, '${programme.durationYears} Years Full-Time'),
                      const SizedBox(width: 10),
                      _buildMetricChip(Icons.grade, 'Min Grade: ${programme.minMeanGrade}'),
                      const SizedBox(width: 10),
                      _buildMetricChip(Icons.analytics, 'Avg: ${programme.averageCutoff} pts'),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Section 1: Overview
            _buildSectionHeader('Programme Overview'),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Text(
                programme.description,
                style: TextStyle(fontSize: 13, color: Colors.grey.shade700, height: 1.5),
              ),
            ),
            const SizedBox(height: 16),

            // Section 2: Minimum Admission & Cluster Prerequisites
            _buildSectionHeader('KUCCPS Subject Prerequisites'),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Cluster Group: ${programme.clusterGroup}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  const SizedBox(height: 8),
                  const Text('Mandatory Subject Thresholds:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.grey)),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: programme.minimumSubjectRequirements.entries.map((entry) {
                      return Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: Colors.blue.shade200),
                        ),
                        child: Text(
                          '${entry.key}: Min ${entry.value}',
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.blue.shade900),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Section 3: Offering Universities & Cutoff Points
            _buildSectionHeader('Accredited Kenyan Universities Offering Programme'),
            ...programme.offeringUniversities.map((uni) {
              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(uni.universityName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          const SizedBox(height: 2),
                          Text('${uni.universityType} • ${uni.location} • KUCCPS Code: ${uni.kuccpsCode}',
                              style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          '${uni.latestCutoff.toStringAsFixed(2)} pts',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF0EA5A4)),
                        ),
                        Text('Prev: ${uni.previousCutoff.toStringAsFixed(2)}', style: TextStyle(fontSize: 10, color: Colors.grey.shade500)),
                      ],
                    ),
                  ],
                ),
              );
            }).toList(),
            const SizedBox(height: 16),

            // Section 4: Career Pathways
            _buildSectionHeader('Career Pathways & Professional Roles'),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: programme.careerOpportunities.map((career) {
                return Chip(
                  backgroundColor: const Color(0xFFF1F5F9),
                  avatar: const Icon(Icons.work_outline, size: 16, color: Color(0xFF14213D)),
                  label: Text(career, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF14213D))),
                );
              }).toList(),
            ),
            const SizedBox(height: 16),

            // Section 5: Professional Certifications
            _buildSectionHeader('Industry Certifications & Professional Bodies'),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: programme.professionalCertifications.map((cert) {
                return Chip(
                  backgroundColor: Colors.purple.shade50,
                  avatar: Icon(Icons.verified, size: 16, color: Colors.purple.shade700),
                  label: Text(cert, style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.purple.shade900)),
                );
              }).toList(),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricChip(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: Colors.grey.shade700),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(fontSize: 11, color: Colors.grey.shade800, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0, top: 4.0),
      child: Text(
        title,
        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
      ),
    );
  }
}
