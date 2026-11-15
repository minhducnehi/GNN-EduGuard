namespace GNN_EduGuard.Models.ViewModels
{
    public class ModelMetricSet
    {
        public string ModelName { get; set; } = string.Empty;
        public double F1Macro { get; set; }
        public double AucRoc { get; set; }
        public double RecallRisk { get; set; }
    }

    public class FeatureImportanceItem
    {
        public string FeatureKey { get; set; } = string.Empty;
        public string FeatureName { get; set; } = string.Empty;
        public double PermutationImportance { get; set; }
        public double ImpurityImportance { get; set; }
    }

    public class DashboardViewModel
    {
        public List<FeatureImportanceItem> FeatureImportances { get; set; } = new();
        public string FeatureImportanceMethod { get; set; } = string.Empty;

        public int TotalStudents { get; set; }
        public int HighRiskCount { get; set; }
        public int ModerateRiskCount { get; set; }
        public int SafeCount { get; set; }

        public double HighRiskPercentage => TotalStudents > 0 ? Math.Round((double)HighRiskCount / TotalStudents * 100, 1) : 0;
        public double ModerateRiskPercentage => TotalStudents > 0 ? Math.Round((double)ModerateRiskCount / TotalStudents * 100, 1) : 0;
        public double SafePercentage => TotalStudents > 0 ? Math.Round((double)SafeCount / TotalStudents * 100, 1) : 0;

        public List<Student> TopHighRiskStudents { get; set; } = new();
        public List<Student> RecentEvaluatedStudents { get; set; } = new();

        public ModelMetricSet BaselineMetrics { get; set; } = new()
        {
            ModelName = "Baseline (Random Forest / Tabular)",
            F1Macro = 0.8889,
            AucRoc = 0.9650,
            RecallRisk = 0.9000
        };

        public ModelMetricSet GnnMetrics { get; set; } = new()
        {
            ModelName = "GNN HGT + Temporal LSTM (Đồ thị học tập)",
            F1Macro = 0.9332,
            AucRoc = 0.9940,
            RecallRisk = 1.0000
        };
    }
}
