using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace SendAgentMetrics
{
    /// <summary>
    /// Sends agent run metrics to the centralized metrics endpoint.
    /// Reads endpoint URL from the AGENT_METRICS_ENDPOINT environment variable.
    /// </summary>
    public class AgentMetricsReporter
    {
        private readonly HttpClient _httpClient;
        private readonly string _endpoint;
        private readonly DateTime _startTime;

        private int _tokenUsage;
        private int _apiCallsCount;

        public AgentMetricsReporter(string agentName, string jobType)
        {
            _endpoint = Environment.GetEnvironmentVariable("AGENT_METRICS_ENDPOINT")
                ?? throw new InvalidOperationException("AGENT_METRICS_ENDPOINT environment variable is not set");

            _httpClient = new HttpClient();
            _startTime = DateTime.UtcNow;

            AgentName = agentName;
            JobType = jobType;
            RunId = $"{agentName.ToLower().Replace(" ", "_")}_{Guid.NewGuid().ToString("N").Substring(0, 8)}";
        }

        public string AgentName { get; set; }
        public string AgentOwner { get; set; } = "Vladimir Litvinchik";
        public string JobType { get; set; }
        public string RunId { get; set; }
        public string Product { get; set; } = "GroupDocs.Total";
        public string Platform { get; set; } = "All";
        public string Website { get; set; } = "groupdocs.com";
        public string WebsiteSection { get; set; } = "Blog";
        public string ItemName { get; set; } = "Translation";

        /// <summary>
        /// Track token usage from an LLM API call.
        /// Call this after each API call to accumulate totals.
        /// </summary>
        public void TrackUsage(int totalTokens)
        {
            _apiCallsCount++;
            _tokenUsage += totalTokens;
        }

        /// <summary>
        /// Send metrics to the endpoint.
        /// </summary>
        public async Task<bool> ReportAsync(string status, int itemsDiscovered, int itemsSucceeded, int itemsFailed)
        {
            var now = DateTime.UtcNow;
            var payload = new AgentMetrics
            {
                Timestamp = now.ToString("yyyy-MM-ddTHH:mm:ss.fffZ"),
                AgentName = AgentName,
                AgentOwner = AgentOwner,
                JobType = JobType,
                RunId = RunId,
                Status = status,
                Product = Product,
                Platform = Platform,
                Website = Website,
                WebsiteSection = WebsiteSection,
                ItemName = ItemName,
                ItemsDiscovered = itemsDiscovered,
                ItemsFailed = itemsFailed,
                ItemsSucceeded = itemsSucceeded,
                RunDurationMs = (int)(now - _startTime).TotalMilliseconds,
                TokenUsage = _tokenUsage,
                ApiCallsCount = _apiCallsCount
            };

            try
            {
                var response = await _httpClient.PostAsJsonAsync(_endpoint, payload);
                if (response.IsSuccessStatusCode)
                {
                    Console.WriteLine($"Metrics reported (run_id: {RunId}, status: {(int)response.StatusCode})");
                    return true;
                }

                Console.Error.WriteLine($"Warning: Metrics endpoint returned {(int)response.StatusCode} {response.ReasonPhrase}");
                return false;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Warning: Failed to report metrics: {ex.Message}");
                return false;
            }
        }
    }

    class AgentMetrics
    {
        [JsonPropertyName("timestamp")] public string Timestamp { get; set; } = "";
        [JsonPropertyName("agent_name")] public string AgentName { get; set; } = "";
        [JsonPropertyName("agent_owner")] public string AgentOwner { get; set; } = "";
        [JsonPropertyName("job_type")] public string JobType { get; set; } = "";
        [JsonPropertyName("run_id")] public string RunId { get; set; } = "";
        [JsonPropertyName("status")] public string Status { get; set; } = "";
        [JsonPropertyName("product")] public string Product { get; set; } = "";
        [JsonPropertyName("platform")] public string Platform { get; set; } = "";
        [JsonPropertyName("website")] public string Website { get; set; } = "";
        [JsonPropertyName("website_section")] public string WebsiteSection { get; set; } = "";
        [JsonPropertyName("item_name")] public string ItemName { get; set; } = "";
        [JsonPropertyName("items_discovered")] public int ItemsDiscovered { get; set; }
        [JsonPropertyName("items_failed")] public int ItemsFailed { get; set; }
        [JsonPropertyName("items_succeeded")] public int ItemsSucceeded { get; set; }
        [JsonPropertyName("run_duration_ms")] public int RunDurationMs { get; set; }
        [JsonPropertyName("token_usage")] public int TokenUsage { get; set; }
        [JsonPropertyName("api_calls_count")] public int ApiCallsCount { get; set; }
    }
}
