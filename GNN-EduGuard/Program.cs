using GNN_EduGuard.Data;
using GNN_EduGuard.Services;
using Microsoft.EntityFrameworkCore;

namespace GNN_EduGuard
{
    public class Program
    {
        public static void Main(string[] args)
        {
            var builder = WebApplication.CreateBuilder(args);

            // 1. Cấu hình kết nối PostgreSQL (Supabase)
            var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
            builder.Services.AddDbContext<ApplicationDbContext>(options =>
                options.UseNpgsql(connectionString));

            // 2. Đăng ký dịch vụ MVC và API Controllers
            builder.Services.AddControllersWithViews();
            
            // 3. Đăng ký Service tầng dữ liệu & suy luận AI
            builder.Services.AddSingleton<IStudentService, MockStudentService>();

            // 4. Đăng ký OpenAPI / Swagger
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
