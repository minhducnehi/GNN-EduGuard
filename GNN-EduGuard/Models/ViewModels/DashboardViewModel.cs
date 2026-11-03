namespace GNN_EduGuard.Models.ViewModels
{
    public class DashboardViewModel
    {
        public int TotalStudents { get; set; }
        public int HighRiskCount { get; set; }
        public int ModerateRiskCount { get; set; }
        public int SafeCount { get; set; }

        public double HighRiskPercentage => TotalStudents > 0 ? Math.Round((double)HighRiskCount / TotalStudents * 100, 1) : 0;
        public double ModerateRiskPercentage => TotalStudents > 0 ? Math.Round((double)ModerateRiskCount / TotalStudents * 100, 1) : 0;
        public double SafePercentage => TotalStudents > 0 ? Math.Round((double)SafeCount / TotalStudents * 100, 1) : 0;

        public List<Student> TopHighRiskStudents { get; set; } = new();
        public List<Student> RecentEvaluatedStudents { get; set; } = new();
    }
}
