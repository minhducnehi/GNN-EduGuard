using System.Security.Claims;
using GNN_EduGuard.Services;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace GNN_EduGuard.Controllers
{
    public class AccountController : Controller
    {
        [AllowAnonymous]
        [HttpGet]
        public IActionResult Login(string? returnUrl = null)
        {
            if (User.Identity?.IsAuthenticated == true)
            {
                if (User.IsInRole("Student"))
                {
                    return RedirectToAction("Details", "Students", new { id = User.GetStudentId() });
                }
                return RedirectToAction("Index", "Home");
            }

            ViewBag.ReturnUrl = returnUrl;
            return View();
        }

        [AllowAnonymous]
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Login(string username, string password, string? returnUrl = null)
        {
            var account = UserAccountStore.Authenticate(username, password);
            if (account == null)
            {
                ViewBag.ReturnUrl = returnUrl;
                ViewBag.LoginError = "Tên đăng nhập hoặc mật khẩu không đúng. Vui lòng kiểm tra lại.";
                return View();
            }

            var claims = new List<Claim>
            {
                new(ClaimTypes.Name, account.DisplayName),
                new(ClaimTypes.Email, account.Email),
                new(ClaimTypes.Role, account.Role),
                new("Username", account.Username),
                new("StudentId", account.StudentId.ToString()),
                new("AssignedClasses", string.Join(",", account.AssignedClasses))
            };

            var identity = new ClaimsIdentity(claims, CookieAuthenticationDefaults.AuthenticationScheme);
            var principal = new ClaimsPrincipal(identity);

            await HttpContext.SignInAsync(
                CookieAuthenticationDefaults.AuthenticationScheme,
                principal,
                new AuthenticationProperties { IsPersistent = true });

            TempData["SuccessMessage"] = account.Role switch
            {
                "Admin" => $"Đăng nhập thành công với quyền Quản trị viên (Admin): {account.DisplayName}.",
                "Advisor" => $"Đăng nhập thành công với quyền Giáo viên: {account.DisplayName} (Lớp phụ trách: {string.Join(", ", account.AssignedClasses)}).",
                _ => $"Xin chào {account.DisplayName}! Bạn đang xem hồ sơ học tập cá nhân."
            };

            if (account.Role == "Student")
            {
                return RedirectToAction("Details", "Students", new { id = account.StudentId });
            }

            if (!string.IsNullOrEmpty(returnUrl) && Url.IsLocalUrl(returnUrl))
            {
                return Redirect(returnUrl);
            }

            return RedirectToAction("Index", "Home");
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Logout()
        {
            await HttpContext.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
            TempData["SuccessMessage"] = "Bạn đã đăng xuất khỏi hệ thống GNN-EduGuard.";
            return RedirectToAction(nameof(Login));
        }

        [AllowAnonymous]
        [HttpGet]
        public IActionResult AccessDenied()
        {
            if (User.Identity?.IsAuthenticated != true)
            {
                return RedirectToAction(nameof(Login));
            }

            if (User.IsInRole("Student"))
            {
                TempData["ErrorMessage"] = "Sinh viên chỉ được phép xem các chỉ số học tập và chuyên cần của chính mình.";
                return RedirectToAction("Details", "Students", new { id = User.GetStudentId() });
            }

            TempData["ErrorMessage"] = "Tài khoản hiện tại không có quyền truy cập chức năng hoặc lớp học này.";
            return RedirectToAction("Index", "Home");
        }
    }
}
