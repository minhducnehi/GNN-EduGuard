using GNN_EduGuard.Services;
using Microsoft.AspNetCore.Mvc;

namespace GNN_EduGuard.Controllers
{
    public class HomeController : Controller
    {
        private readonly IStudentService _studentService;

        public HomeController(IStudentService studentService)
        {
            _studentService = studentService;
        }

        public IActionResult Index()
        {
            var dashboardData = _studentService.GetDashboardData();
            return View(dashboardData);
        }

        public IActionResult Privacy()
        {
            return View();
        }
    }
}
