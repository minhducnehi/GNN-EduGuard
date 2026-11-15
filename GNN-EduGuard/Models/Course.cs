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

    public class SubgraphExplanationItem
    {
        public string EdgeType { get; set; } = string.Empty;
        public string AssignmentNode { get; set; } = string.Empty;
        public string ConceptNode { get; set; } = string.Empty;
        public double RiskContribution { get; set; }
        public string Explanation { get; set; } = string.Empty;
    }

    public class WeeklyTrajectoryPoint
    {
        public int Week { get; set; }
        public double RiskScore { get; set; }
        public string Status { get; set; } = string.Empty;
    }

    public class InterventionLog
    {
        public int Id { get; set; }
        public int StudentId { get; set; }
        public string AdvisorName { get; set; } = "CVHT. Nguyễn Minh Đức";
        public string ActionType { get; set; } = "Tư vấn 1-1";
        public string Notes { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; } = DateTime.Now;
    }

    public class RiskPredictionDetail
    {
        public Student Student { get; set; } = null!;
        public List<RiskExplanation> Explanations { get; set; } = new();
        public List<SubgraphExplanationItem> SubgraphExplanations { get; set; } = new();
        public List<WeeklyTrajectoryPoint> EarlyWarningTrajectory { get; set; } = new();
        public List<string> WeakConcepts { get; set; } = new();
        public List<string> RecommendedActions { get; set; } = new();
        public List<InterventionLog> InterventionHistory { get; set; } = new();
    }
}
