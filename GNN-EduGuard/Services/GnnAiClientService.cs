using System.Net.Http.Json;
using System.Text.Json;
using GNN_EduGuard.Models;
using GNN_EduGuard.Models.ViewModels;

namespace GNN_EduGuard.Services
{
    public class GnnAiClientService : IStudentService
    {
        private readonly HttpClient _httpClient;
        private readonly MockStudentService _fallbackService;
        private readonly ILogger<GnnAiClientService> _logger;

        public GnnAiClientService(HttpClient httpClient, IConfiguration configuration, ILogger<GnnAiClientService> logger)
        {
            _httpClient = httpClient;
            var baseUrl = Environment.GetEnvironmentVariable("AI_SERVICE_URL")
                          ?? configuration["AiService:BaseUrl"]
                          ?? "http://127.0.0.1:8000";
            _httpClient.BaseAddress = new Uri(baseUrl);
            _httpClient.Timeout = TimeSpan.FromSeconds(30);
            _fallbackService = new MockStudentService();
            _logger = logger;
        }

        public async Task<DashboardViewModel> GetDashboardDataAsync()
        {
            var dashboard = await _fallbackService.GetDashboardDataAsync();
            await LoadFeatureImportanceAsync(dashboard);

            try
            {
                var bench = await _httpClient.GetFromJsonAsync<JsonElement>("/api/models/benchmark");
                if (bench.ValueKind == JsonValueKind.Object)
                {
                    ApplyBenchmarkJson(dashboard, bench);
                    return dashboard;
                }
            }
            catch
            {
                try
                {
                    var localPath = Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "..", "ai-service", "gnn", "data", "processed", "benchmark_summary.json"));
                    if (File.Exists(localPath))
                    {
                        var rawJson = await File.ReadAllTextAsync(localPath);
                        var bench = JsonSerializer.Deserialize<JsonElement>(rawJson);
                        ApplyBenchmarkJson(dashboard, bench);
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogDebug("Could not load local benchmark_summary.json: {Message}", ex.Message);
                }
            }

            return dashboard;
        }

        private async Task LoadFeatureImportanceAsync(DashboardViewModel dashboard)
        {
            JsonElement fi = default;
            try
            {
                fi = await _httpClient.GetFromJsonAsync<JsonElement>("/api/models/feature-importance");
            }
            catch
            {
                try
                {
                    var localPath = Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "..", "ai-service", "gnn", "data", "processed", "feature_importance.json"));
                    if (File.Exists(localPath))
                    {
                        fi = JsonSerializer.Deserialize<JsonElement>(await File.ReadAllTextAsync(localPath));
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogDebug("Could not load local feature_importance.json: {Message}", ex.Message);
                }
            }
            ApplyFeatureImportanceJson(dashboard, fi);
        }

        internal static void ApplyFeatureImportanceJson(DashboardViewModel dashboard, JsonElement fi)
        {
            if (fi.ValueKind != JsonValueKind.Object) return;
            if (fi.TryGetProperty("method", out var method) && method.ValueKind == JsonValueKind.String)
            {
                dashboard.FeatureImportanceMethod = method.GetString() ?? string.Empty;
            }
            if (!fi.TryGetProperty("features", out var feats) || feats.ValueKind != JsonValueKind.Array) return;

            dashboard.FeatureImportances.Clear();
            foreach (var item in feats.EnumerateArray())
            {
                dashboard.FeatureImportances.Add(new FeatureImportanceItem
                {
                    FeatureKey = item.TryGetProperty("feature_key", out var k) ? k.GetString() ?? "" : "",
                    FeatureName = item.TryGetProperty("feature_name", out var n) ? n.GetString() ?? "" : "",
                    PermutationImportance = item.TryGetProperty("permutation_importance", out var p) && p.ValueKind == JsonValueKind.Number ? p.GetDouble() : 0.0,
                    ImpurityImportance = item.TryGetProperty("rf_impurity_importance", out var r) && r.ValueKind == JsonValueKind.Number ? r.GetDouble() : 0.0
                });
            }
        }

        private static void ApplyBenchmarkJson(DashboardViewModel dashboard, JsonElement bench)
        {
            if (bench.TryGetProperty("Random Forest", out var rf))
            {
                dashboard.BaselineMetrics = new ModelMetricSet
                {
                    ModelName = "Baseline (Random Forest / Tabular)",
                    F1Macro = rf.TryGetProperty("f1_macro", out var f1) ? f1.GetDouble() : 0.88,
                    AucRoc = rf.TryGetProperty("auc_roc", out var auc) ? auc.GetDouble() : 0.95,
                    RecallRisk = rf.TryGetProperty("recall_risk", out var rec) ? rec.GetDouble() : 0.90
                };
            }

            if (bench.TryGetProperty("HGT + LSTM (Temporal)", out var hgtTemp))
            {
                dashboard.GnnMetrics = new ModelMetricSet
                {
                    ModelName = "GNN HGT + Temporal LSTM (Điểm danh & Đồ thị)",
                    F1Macro = hgtTemp.TryGetProperty("f1_macro", out var f1) ? f1.GetDouble() : 0.93,
                    AucRoc = hgtTemp.TryGetProperty("auc_roc", out var auc) ? auc.GetDouble() : 0.99,
                    RecallRisk = hgtTemp.TryGetProperty("recall_risk", out var rec) ? rec.GetDouble() : 1.00
                };
            }
            else if (bench.TryGetProperty("HGT (HeteroGNN)", out var hgt))
            {
                dashboard.GnnMetrics = new ModelMetricSet
                {
                    ModelName = "GNN HeteroGNN / HGT (Điểm danh & Đồ thị)",
                    F1Macro = hgt.TryGetProperty("f1_macro", out var f1) ? f1.GetDouble() : 0.93,
                    AucRoc = hgt.TryGetProperty("auc_roc", out var auc) ? auc.GetDouble() : 0.98,
                    RecallRisk = hgt.TryGetProperty("recall_risk", out var rec) ? rec.GetDouble() : 1.00
                };
            }
        }

        public Task<List<Student>> GetAllStudentsAsync(string? search = null, RiskLevel? riskFilter = null)
        {
            return _fallbackService.GetAllStudentsAsync(search, riskFilter);
        }

        public Task<Student?> GetStudentByIdAsync(int id)
        {
            return _fallbackService.GetStudentByIdAsync(id);
        }

        public async Task<RiskPredictionDetail?> GetStudentRiskDetailAsync(int id)
        {
            var fallback = await _fallbackService.GetStudentRiskDetailAsync(id);
            if (fallback == null) return null;

            try
            {
                // Sync current student attendance to Python GNN and get live prediction
                var payload = new
                {
                    attended_sessions = fallback.Student.AttendedSessions,
                    total_sessions = fallback.Student.TotalSessions
                };
                var resp = await _httpClient.PostAsJsonAsync($"/api/predict/attendance/{id}", payload);
                if (resp.IsSuccessStatusCode)
                {
                    var response = await resp.Content.ReadFromJsonAsync<JsonElement>();
                    PopulateDetailFromGnnResponse(id, fallback, response);
                }
                else
                {
                    var response = await _httpClient.GetFromJsonAsync<JsonElement>($"/api/predict/risk/{id}");
                    PopulateDetailFromGnnResponse(id, fallback, response);
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning("FastAPI AI Service offline or timed out, using fallback: {Message}", ex.Message);
            }

            return fallback;
        }

        private void PopulateDetailFromGnnResponse(int id, RiskPredictionDetail fallback, JsonElement response)
        {
            if (response.ValueKind == JsonValueKind.Undefined) return;

            int? attended = null;
            int? total = null;
            if (response.TryGetProperty("attended_sessions", out var attProp))
            {
                attended = attProp.GetInt32();
                fallback.Student.AttendedSessions = attended.Value;
            }
            if (response.TryGetProperty("total_sessions", out var totProp))
            {
                total = totProp.GetInt32();
                fallback.Student.TotalSessions = total.Value;
            }

            double newProb = fallback.Student.RiskProbability;
            if (response.TryGetProperty("risk_score", out var scoreProp))
            {
                newProb = scoreProp.GetDouble();
                fallback.Student.RiskProbability = newProb;
                fallback.Student.RiskLevel = MockStudentService.ClassifyRisk(newProb);
            }

            string? topReason = null;
            if (response.TryGetProperty("reasons", out var reasonsProp) && reasonsProp.ValueKind == JsonValueKind.Array)
            {
                foreach (var r in reasonsProp.EnumerateArray())
                {
                    topReason = r.GetString();
                    if (!string.IsNullOrWhiteSpace(topReason)) break;
                }
            }

            _fallbackService.SyncStudentPrediction(id, newProb, topReason, attended, total);

            // 1. Populate GNN XAI Feature Attributions (including Class Attendance Rate)
            if (response.TryGetProperty("feature_attributions", out var attrProp) && attrProp.ValueKind == JsonValueKind.Array)
            {
                fallback.Explanations.Clear();
                foreach (var item in attrProp.EnumerateArray())
                {
                    fallback.Explanations.Add(new RiskExplanation
                    {
                        FeatureName = item.TryGetProperty("feature_name", out var fn) ? fn.GetString() ?? "GNN Feature" : "GNN Feature",
                        Description = item.TryGetProperty("description", out var desc) ? desc.GetString() ?? "" : "",
                        ImpactScore = item.TryGetProperty("impact_score", out var imp) ? imp.GetDouble() : 0.0,
                        IsNegativeImpact = item.TryGetProperty("is_negative_impact", out var neg) && neg.GetBoolean()
                    });
                }
            }

            // 2. Populate 2-Hop Subgraph Explanations + Attendance Rules
            if (response.TryGetProperty("subgraph_explanations", out var subProp) && subProp.ValueKind == JsonValueKind.Array)
            {
                fallback.SubgraphExplanations.Clear();
                foreach (var item in subProp.EnumerateArray())
                {
                    fallback.SubgraphExplanations.Add(new SubgraphExplanationItem
                    {
                        EdgeType = item.TryGetProperty("edge_type", out var et) ? et.GetString() ?? "" : "",
                        AssignmentNode = item.TryGetProperty("assignment_node", out var an) ? an.GetString() ?? "" : "",
                        ConceptNode = item.TryGetProperty("concept_node", out var cn) ? cn.GetString() ?? "" : "",
                        RiskContribution = item.TryGetProperty("risk_contribution", out var rc) ? rc.GetDouble() : 0.0,
                        Explanation = item.TryGetProperty("explanation", out var ex) ? ex.GetString() ?? "" : ""
                    });
                }
            }

            // 3. Populate Early Warning Weekly Trajectory (Weeks 2, 4, 8, 12, 16)
            if (response.TryGetProperty("early_warning_trajectory", out var trajProp) && trajProp.ValueKind == JsonValueKind.Array)
            {
                fallback.EarlyWarningTrajectory.Clear();
                foreach (var item in trajProp.EnumerateArray())
                {
                    fallback.EarlyWarningTrajectory.Add(new WeeklyTrajectoryPoint
                    {
                        Week = item.TryGetProperty("week", out var wk) ? wk.GetInt32() : 0,
                        RiskScore = item.TryGetProperty("risk_score", out var rs) ? rs.GetDouble() : 0.0,
                        Status = item.TryGetProperty("status", out var st) ? st.GetString() ?? "Low" : "Low"
                    });
                }
            }

            // 4. Populate Weak Concepts
            if (response.TryGetProperty("weak_concepts", out var weakProp) && weakProp.ValueKind == JsonValueKind.Array)
            {
                fallback.WeakConcepts.Clear();
                foreach (var c in weakProp.EnumerateArray())
                {
                    var cName = c.GetString();
                    if (!string.IsNullOrEmpty(cName))
                    {
                        fallback.WeakConcepts.Add(cName);
                        fallback.RecommendedActions.Insert(0, $"Ôn tập củng cố khái niệm: {cName} (phát hiện từ đồ thị môn học & buổi vắng)");
                    }
                }
            }
        }

        public async Task UpdateStudentAttendanceAsync(int studentId, int attendedSessions, int totalSessions = 9)
        {
            await _fallbackService.UpdateStudentAttendanceAsync(studentId, attendedSessions, totalSessions);

            try
            {
                var payload = new
                {
                    attended_sessions = attendedSessions,
                    total_sessions = totalSessions
                };
                var resp = await _httpClient.PostAsJsonAsync($"/api/predict/attendance/{studentId}", payload);
                if (resp.IsSuccessStatusCode)
                {
                    var json = await resp.Content.ReadFromJsonAsync<JsonElement>();
                    if (json.ValueKind != JsonValueKind.Undefined && json.TryGetProperty("risk_score", out var scoreProp))
                    {
                        string? topReason = null;
                        if (json.TryGetProperty("reasons", out var rProp) && rProp.ValueKind == JsonValueKind.Array)
                        {
                            foreach (var r in rProp.EnumerateArray())
                            {
                                topReason = r.GetString();
                                if (!string.IsNullOrWhiteSpace(topReason)) break;
                            }
                        }
                        _fallbackService.SyncStudentPrediction(studentId, scoreProp.GetDouble(), topReason, attendedSessions, totalSessions);
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning("Could not sync attendance update to FastAPI for student {Id}: {Message}", studentId, ex.Message);
            }
        }

        public async Task ReEvaluateStudentRiskAsync(int id)
        {
            await _fallbackService.ReEvaluateStudentRiskAsync(id);
            var student = await _fallbackService.GetStudentByIdAsync(id);
            if (student != null)
            {
                await UpdateStudentAttendanceAsync(id, student.AttendedSessions, student.TotalSessions);
            }
        }

        public Task AddInterventionLogAsync(int studentId, string advisorName, string actionType, string notes)
        {
            return _fallbackService.AddInterventionLogAsync(studentId, advisorName, actionType, notes);
        }

        public Task<byte[]> ExportStudentsCsvAsync(string? search = null, RiskLevel? riskFilter = null)
        {
            return _fallbackService.ExportStudentsCsvAsync(search, riskFilter);
        }
    }
}
