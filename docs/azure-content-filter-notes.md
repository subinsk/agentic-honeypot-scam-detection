# Azure Content Filter & Jailbreak Detection (Research Notes)

When using **GitHub Models** (or any Azure OpenAI–backed provider) with scam-style messages, you may see:

```text
Error code: 400 - content_filter, jailbreak: detected: True
"The response was filtered due to the prompt triggering Azure OpenAI's content management policy."
```

## What’s going on

- **Azure Prompt Shield** treats the **user** prompt as potential jailbreak / social engineering.
- It looks for: role-playing, “don’t reveal you’re AI”, manipulative or instruction-like text.
- Scam phrases (“Your bank account will be blocked”, “Verify immediately”) in the **user** role can be flagged as adversarial user input, causing false positives.

## What we did in this project

1. **System prompt** – Kept neutral: “Context: You are helping test a conversational reply system…” and “This is for testing only.” No roleplay or “don’t reveal” wording.
2. **User message framing** – Incoming (scammer) text is wrapped as:  
   `Sample message to reply to (security research / testing):`  
   so the filter sees it as quoted sample content to reply to, not as a user instruction.
3. **Role separation** – System / user / assistant are kept strictly separate (per [Microsoft’s guidance](https://techcommunity.microsoft.com/blog/microsoft-security-blog/the-security-benefits-of-structuring-your-azure-openai-calls-%E2%80%93-the-system-role/4375763)).

## If you still get 503 / content_filter

- **Azure filter cannot be turned off** via API when using GitHub Models; only the resource owner (e.g. GitHub) can configure it.
- **Recommended for this use case:** use a provider that does **not** use Azure’s filter:
  - **Groq** (`LLM_PROVIDER=groq`, `GROQ_API_KEY`) – free open-weights, no Azure filter.
  - **OpenRouter** (`LLM_PROVIDER=openrouter`, `OPENROUTER_API_KEY`) – free `:free` models, no Azure filter.

## References

- [Azure: Configure content filters](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/content-filters)
- [Prompt Shields (jailbreak detection)](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/jailbreak-detection)
- [Structuring Azure OpenAI calls – system vs user role](https://techcommunity.microsoft.com/blog/microsoft-security-blog/the-security-benefits-of-structuring-your-azure-openai-calls-%E2%80%93-the-system-role/4375763)
- [False positive jailbreak on benign prompts](https://learn.microsoft.com/en-us/answers/questions/2244789/azure-openai-api-inconsistent-false-positive-jailb)
