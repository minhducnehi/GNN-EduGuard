using GNN_EduGuard.Models;
using GNN_EduGuard.Models.ViewModels;

namespace GNN_EduGuard.Services
{
    public interface IStudentService
    {
        DashboardViewModel GetDashboardData();
        List<Student> GetAllStudents(string? search = null, RiskLevel? riskFilter = null);
        Student? GetStudentById(int id);
        RiskPredictionDetail? GetStudentRiskDetail(int id);
        void ReEvaluateStudentRisk(int id);
    }
}
