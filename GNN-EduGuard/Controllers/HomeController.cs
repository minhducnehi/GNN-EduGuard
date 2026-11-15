using GNN_EduGuard.Models;
using GNN_EduGuard.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace GNN_EduGuard.Controllers
{
    [Authorize]
    public class HomeController : Controller
    {
        private readonly IStudentService _studentService;

        public HomeController(IStudentService studentService)
        {
            _studentService = studentService;
        }

        public async Task<IActionResult> Index()
        {
            if (User.IsInRole("Student"))
            {
                return RedirectToAction("Details", "Students", new { id = User.GetStudentId() });
            }

            var dashboardData = await _studentService.GetDashboardDataAsync();

            if (User.IsInRole("Advisor"))
            {
                var allStudents = await _studentService.GetAllStudentsAsync();
                var scoped = User.FilterByRoleScope(allStudents);

                dashboardData.TotalStudents = scoped.Count;
                dashboardData.HighRiskCount = scoped.Count(s => s.RiskLevel == RiskLevel.HighRisk);
                dashboardData.ModerateRiskCount = scoped.Count(s => s.RiskLevel == RiskLevel.Moderate);
                dashboardData.SafeCount = scoped.Count(s => s.RiskLevel == RiskLevel.Safe);
                dashboardData.TopHighRiskStudents = scoped
                    .Where(s => s.RiskLevel == RiskLevel.HighRisk)
                    .OrderByDescending(s => s.RiskProbability)
                    .Take(5)
                    .ToList();
                dashboardData.RecentEvaluatedStudents = scoped
                    .OrderByDescending(s => s.LastEvaluatedAt)
                    .Take(5)
                    .ToList();
            }

            return View(dashboardData);
        }

        public IActionResult Privacy()
        {
            return View();
        }
    }
}
