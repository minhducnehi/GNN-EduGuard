using System.Security.Claims;
using GNN_EduGuard.Models;

namespace GNN_EduGuard.Services
{
    public record AppUserAccount(
        string Username,
        string Password,
        string DisplayName,
        string Email,
        string Role,
        int StudentId,
        string[] AssignedClasses);

    public static class UserAccountStore
    {
        public static readonly IReadOnlyList<AppUserAccount> Accounts = new List<AppUserAccount>
        {
            // Role 1: Admin - Toàn quyền quản lý hệ thống & tất cả các lớp
            new("admin", "123456", "PĐT. Quản trị Học vụ", "daotao@edu.vn", "Admin", 0, Array.Empty<string>()),

            // Role 2: Giáo viên / Cố vấn Học tập (Advisor) - Quản lý sinh viên được cấp theo lớp
            new("gv.cntta", "123456", "GV. Nguyễn Minh Đức", "duc.nguyen@edu.vn", "Advisor", 0, new[] { "CNTT-K23A", "CNTT-K23B" }),
            new("gv.cnttc", "123456", "GV. Lê Thị Hương", "huong.le@edu.vn", "Advisor", 0, new[] { "CNTT-K23C" }),

            // Role 3: Sinh viên (Student) - Chỉ xem các chỉ số liên quan đến chính sinh viên đó
            new("sv2380601", "123456", "Nguyễn Văn An (SV2380601)", "an.nguyen@edu.vn", "Student", 1, new[] { "CNTT-K23A" }),
            new("sv2380602", "123456", "Trần Thị Mai (SV2380602)", "mai.tran@edu.vn", "Student", 2, new[] { "CNTT-K23A" }),
            new("sv2380606", "123456", "Võ Quốc Cường (SV2380606)", "cuong.vo@edu.vn", "Student", 6, new[] { "CNTT-K23C" })
        };

        public static AppUserAccount? Authenticate(string? username, string? password)
        {
            if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(password))
                return null;

            var normalized = username.Trim();
            return Accounts.FirstOrDefault(u =>
                string.Equals(u.Username, normalized, StringComparison.OrdinalIgnoreCase) &&
                u.Password == password);
        }
    }

    public static class ClaimsPrincipalExtensions
    {
        public static int GetStudentId(this ClaimsPrincipal user)
        {
            var raw = user.FindFirst("StudentId")?.Value;
            return int.TryParse(raw, out var id) ? id : 0;
        }

        public static HashSet<string> GetAssignedClasses(this ClaimsPrincipal user)
        {
            var raw = user.FindFirst("AssignedClasses")?.Value ?? string.Empty;
            return raw.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
                .ToHashSet(StringComparer.OrdinalIgnoreCase);
        }

        public static bool CanAccessStudent(this ClaimsPrincipal user, Student student)
        {
            if (user.IsInRole("Admin")) return true;
            if (user.IsInRole("Advisor")) return user.GetAssignedClasses().Contains(student.ClassName);
            if (user.IsInRole("Student")) return student.Id == user.GetStudentId();
            return false;
        }

        public static List<Student> FilterByRoleScope(this ClaimsPrincipal user, IEnumerable<Student> students)
        {
            if (user.IsInRole("Admin")) return students.ToList();
            if (user.IsInRole("Advisor"))
            {
                var classes = user.GetAssignedClasses();
                return students.Where(s => classes.Contains(s.ClassName)).ToList();
            }
            if (user.IsInRole("Student"))
            {
                var studentId = user.GetStudentId();
                return students.Where(s => s.Id == studentId).ToList();
            }
            return new List<Student>();
        }
    }
}
