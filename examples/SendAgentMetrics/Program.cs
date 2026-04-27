// Example: Send Agent Metrics to the centralized endpoint.
//
// Usage:
//   set AGENT_METRICS_ENDPOINT=https://your-endpoint/api/agent-runs
//   dotnet run

using System;
using System.Threading.Tasks;

namespace SendAgentMetrics
{
    class Program
    {
        static async Task Main(string[] args)
        {
            // 1. Create reporter (starts the duration timer automatically)
            var reporter = new AgentMetricsReporter("Docs Translator", "test")
            {
                Product = "GroupDocs.Total",
                Platform = "All",
                ItemName = "Translation"
            };

            // 2. Do your agent work, tracking tokens along the way
            int succeeded = 0, failed = 0, discovered = 10;

            for (int i = 0; i < discovered; i++)
            {
                // ... your LLM call here ...
                int tokensUsed = 420; // from response.Usage.TotalTokens
                reporter.TrackUsage(tokensUsed);

                if (i < 8)
                    succeeded++;
                else
                    failed++;
            }

            // 3. Report at the end
            await reporter.ReportAsync("success", discovered, succeeded, failed);
        }
    }
}
