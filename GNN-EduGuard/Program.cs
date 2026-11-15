using System.Security.Claims;
using GNN_EduGuard.Data;
using GNN_EduGuard.Services;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.EntityFrameworkCore;

namespace GNN_EduGuard
{
    public class Program
    {
        private static void LoadDotEnv()
        {
            var candidatePaths = new[]
            {
                Path.Combine(Directory.GetCurrentDirectory(), ".env"),
                Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "..", ".env"))
            };

            foreach (var envPath in candidatePaths)
            {
                if (!File.Exists(envPath)) continue;
                foreach (var rawLine in File.ReadAllLines(envPath))
                {
                    var line = rawLine.Trim();
                    if (string.IsNullOrEmpty(line) || line.StartsWith('#')) continue;
                    var sepIdx = line.IndexOf('=');
                    if (sepIdx <= 0) continue;
                    var key = line[..sepIdx].Trim();
                    var val = line[(sepIdx + 1)..].Trim();
                    Environment.SetEnvironmentVariable(key, val);
                }
                break;
            }
        }

        public static void Main(string[] args)
        {
            // 0. Nạp biến môi trường từ file .env (ẩn mật khẩu khỏi appsettings.json)
            LoadDotEnv();

            var builder = WebApplication.CreateBuilder(args);
            builder.Configuration.AddEnvironmentVariables();

            // 1. Cấu hình kết nối PostgreSQL (Supabase từ biến môi trường .env)
            var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
            builder.Services.AddDbContext<ApplicationDbContext>(options =>
                options.UseNpgsql(connectionString));

            // 2. Cấu hình Xác thực & Phân quyền theo Vai trò (RBAC: Admin, Advisor, Student)
            builder.Services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
                .AddCookie(options =>
                {
                    options.LoginPath = "/Account/Login";
                    options.AccessDeniedPath = "/Account/AccessDenied";
                    options.ExpireTimeSpan = TimeSpan.FromHours(8);
                });
            builder.Services.AddAuthorization();

            // 3. Đăng ký dịch vụ MVC và API Controllers
            builder.Services.AddControllersWithViews();

            // 4. Đăng ký Service tầng dữ liệu & suy luận AI (Async HttpClient kết nối FastAPI Python)
            builder.Services.AddHttpClient<IStudentService, GnnAiClientService>();
            builder.Services.AddScoped<IEmailService, GmailSmtpEmailService>();
            builder.Services.AddHttpClient("AiEngine", client =>
            {
                var baseUrl = Environment.GetEnvironmentVariable("AI_SERVICE_URL")
                              ?? builder.Configuration["AiService:BaseUrl"]
                              ?? "http://127.0.0.1:8000";
                client.BaseAddress = new Uri(baseUrl);
                client.Timeout = TimeSpan.FromSeconds(45);
            });

            // 5. Đăng ký OpenAPI / Swagger
            builder.Services.AddOpenApi();

            var app = builder.Build();

            // Cấu hình HTTP request pipeline
            if (app.Environment.IsDevelopment())
            {
                app.MapOpenApi();
            }

            app.UseHttpsRedirection();
            app.UseStaticFiles();

            app.UseRouting();

            app.UseAuthentication();
            app.UseAuthorization();

            // Cấu hình Route chuẩn MVC (Home/Index)
            app.MapControllerRoute(
                name: "default",
                pattern: "{controller=Home}/{action=Index}/{id?}");

            // Đồng thời map các API Controllers (/api/predictionsapi/...)
            app.MapControllers();

            app.Run();
        }
    }
}
