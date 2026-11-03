namespace GNN_EduGuard.Models
{
    public enum RiskLevel
    {
        Safe = 0,       // An toàn (< 40%)
        Moderate = 1,   // Nguy cơ vừa (40% - 70%)
        HighRisk = 2    // Nguy cơ cao (> 70%)
    }

    public class Student
    {
        public int Id { get; set; }
        public string StudentCode { get; set; } = string.Empty;
        public string FullName { get; set; } = string.Empty;
        public string Email { get; set; } = string.Empty;
        public string ClassName { get; set; } = string.Empty;
        public string Gender { get; set; } = string.Empty;
        public int Age { get; set; }
        public double GpaBefore { get; set; }
        public int TotalVleClicks { get; set; }
        public double LateSubmissionRate { get; set; } // 0.0 - 1.0 (0% - 100%)
        public double AssignmentAverageScore { get; set; } // Thang 100
        
        // GNN Model Inference Outputs
        public double RiskProbability { get; set; } // 0.0 - 1.0
        public RiskLevel RiskLevel { get; set; }
        public string TopRiskFactor { get; set; } = string.Empty;
        public DateTime LastEvaluatedAt { get; set; } = DateTime.Now;
    }
}
