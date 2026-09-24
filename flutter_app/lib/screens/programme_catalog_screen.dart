import 'package:flutter/material.dart';
import '../models/programme.dart';
import '../data/programme_repository.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';
import 'programme_detail_screen.dart';

class ProgrammeCatalogScreen extends StatefulWidget {
  const ProgrammeCatalogScreen({Key? key}) : super(key: key);

  @override
  State<ProgrammeCatalogScreen> createState() => _ProgrammeCatalogScreenState();
}

class _ProgrammeCatalogScreenState extends State<ProgrammeCatalogScreen> {
  String _selectedCategory = 'All';
  String _searchQuery = '';

  List<Programme> _programmes = ProgrammeRepository.allProgrammes;
  bool _isLoading = true;
  bool _usingOfflineFallback = false;

  final List<String> _categories = [
    'All',
    'Medicine & Health',
    'Computing & IT',
    'Engineering',
    'Law',
    'Business & Finance',
  ];

  @override
  void initState() {
    super.initState();
    _loadProgrammes();
  }

  Future<void> _loadProgrammes() async {
    setState(() => _isLoading = true);
    try {
      final live = await ApiService.fetchProgrammes();
      setState(() {
        _programmes = live;
        _usingOfflineFallback = false;
        _isLoading = false;
      });
    } on ApiException {
      // Server unreachable: fall back to the bundled catalog rather than
      // showing an empty directory. Real data, just possibly stale cutoffs.
      setState(() {
        _programmes = ProgrammeRepository.allProgrammes;
        _usingOfflineFallback = true;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final filtered = _programmes.where((prog) {
      final matchesSearch = prog.title.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          prog.code.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          prog.faculty.toLowerCase().contains(_searchQuery.toLowerCase());

      if (!matchesSearch) return false;

      if (_selectedCategory == 'All') return true;
      if (_selectedCategory == 'Medicine & Health' && prog.clusterGroup.contains('Medicine')) return true;
      if (_selectedCategory == 'Computing & IT' && prog.clusterGroup.contains('Computing')) return true;
      if (_selectedCategory == 'Engineering' && prog.clusterGroup.contains('Engineering')) return true;
      if (_selectedCategory == 'Law' && prog.clusterGroup.contains('Law')) return true;
      if (_selectedCategory == 'Business & Finance' && (prog.clusterGroup.contains('Business') || prog.clusterGroup.contains('Finance'))) return true;

      return false;
    }).toList();

    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground(context),
      appBar: AppBar(
        title: const Text(
          'University Programme Directory',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        backgroundColor: const Color(0xFF14213D),
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _loadProgrammes,
          ),
        ],
      ),
      body: Column(
        children: [
          if (_isLoading)
            const LinearProgressIndicator(
              minHeight: 2,
              color: Color(0xFF0EA5A4),
              backgroundColor: Color(0xFF14213D),
            ),
          if (_usingOfflineFallback)
            Container(
              width: double.infinity,
              color: Colors.amber.shade50,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  Icon(Icons.cloud_off, size: 14, color: Colors.amber.shade800),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      'Server unreachable - showing the bundled catalog, cutoffs may be out of date.',
                      style: TextStyle(fontSize: 11, color: Colors.amber.shade900),
                    ),
                  ),
                ],
              ),
            ),
          // Search & Filter Header
          Container(
            color: const Color(0xFF14213D),
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: Column(
              children: [
                TextField(
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                  decoration: InputDecoration(
                    hintText: 'Search by programme title or faculty...',
                    hintStyle: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                    prefixIcon: const Icon(Icons.search, color: Color(0xFF0EA5A4), size: 20),
                    filled: true,
                    fillColor: const Color(0xFF1E293B),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: BorderSide.none,
                    ),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    isDense: true,
                  ),
                  onChanged: (val) => setState(() => _searchQuery = val),
                ),
                const SizedBox(height: 12),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: _categories.map((cat) {
                      final isSelected = _selectedCategory == cat;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8.0),
                        child: ChoiceChip(
                          label: Text(
                            cat,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                              color: isSelected ? Colors.white : const Color(0xFFCBD5E1),
                            ),
                          ),
                          selected: isSelected,
                          selectedColor: const Color(0xFF0EA5A4),
                          backgroundColor: const Color(0xFF1E293B),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                          onSelected: (_) => setState(() => _selectedCategory = cat),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ],
            ),
          ),

          // Programme List
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: filtered.length,
              itemBuilder: (context, index) {
                final prog = filtered[index];
                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: AppColors.cardBackground(context),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.cardBorder(context)),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.02),
                        blurRadius: 6,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    title: Text(
                      prog.title,
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.textPrimary(context)),
                    ),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 4),
                        Text(
                          '${prog.faculty} • ${prog.durationYears} Years',
                          style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context)),
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: const Color(0xFF0EA5A4).withOpacity(0.12),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                'Cutoff: ${prog.averageCutoff} pts',
                                style: const TextStyle(color: Color(0xFF0EA5A4), fontSize: 11, fontWeight: FontWeight.bold),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Min: ${prog.minMeanGrade}',
                              style: TextStyle(fontSize: 11, color: AppColors.textSecondary(context), fontWeight: FontWeight.w600),
                            ),
                          ],
                        ),
                      ],
                    ),
                    trailing: const Icon(Icons.chevron_right, color: Colors.grey),
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => ProgrammeDetailScreen(programme: prog),
                        ),
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
