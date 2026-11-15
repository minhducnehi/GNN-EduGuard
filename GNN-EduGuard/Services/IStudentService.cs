using GNN_EduGuard.Models;
using GNN_EduGuard.Models.ViewModels;

namespace GNN_EduGuard.Services
{
    public interface IStudentService
    {
        Task<DashboardViewModel> GetDashboardDataAsync();
        Task<List<Student>> GetAllStudentsAsync(string? search = null, RiskLevel? riskFilter = null);
        Task<Student?> GetStudentByIdAsync(int id);
        Task<RiskPredictionDetail?> GetStudentRiskDetailAsync(int id);
        Task ReEvaluateStudentRiskAsync(int id);
        Task UpdateStudentAttendanceAsync(int studentId, int attendedSessions, int totalSessions = 9);
        Task AddInterventionLogAsync(int studentId, string advisorName, string actionType, string notes);
        Task<byte[]> ExportStudentsCsvAsync(string? search = null, RiskLevel? riskFilter = null);
    }
}
