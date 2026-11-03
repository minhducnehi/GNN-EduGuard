namespace GNN_EduGuard.Models
{
    public class Course
    {
        public int Id { get; set; }
        public string CourseCode { get; set; } = string.Empty;
        public string CourseName { get; set; } = string.Empty;
        public int Credits { get; set; }
        public double DifficultyRate { get; set; } // 0.0 - 1.0
        public int EnrolledStudentsCount { get; set; }
    }

    public class RiskExplanation
    {
        public string FeatureName { get; set; } = string.Empty;
        public double ImpactScore { get; set; } // Tác động SHAP / Attention (+ tăng nguy cơ, - giảm nguy cơ)
        public string Description { get; set; } = string.Empty;
        public bool IsNegativeImpact { get; set; }
    }

    public class RiskPredictionDetail
    {
        public Student Student { get; set; } = null!;
        public List<RiskExplanation> Explanations { get; set; } = new();
        public List<string> RecommendedActions { get; set; } = new();
    }
}
