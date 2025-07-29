---
icon: material/speedometer
---

# Rate Limits

DeepSeek's chat interface presents an interesting situation when it comes to rate limits. On paper, there aren't any official restrictions on how much you can use the service. In practice, you might occasionally hit some invisible boundaries that IntenseRP Next can't work around.

## The Unofficial Limits

Most of the time, you can chat away without any issues. DeepSeek doesn't advertise specific rate limits for their chat interface, and many users never encounter any restrictions at all. However, the service does have some protective measures in place.

If DeepSeek's systems detect what they consider "abusive" usage patterns, you might find yourself temporarily blocked. What counts as abuse isn't clearly defined, but rapid-fire requests or extremely heavy usage could trigger these protections.

## The Mysterious "Server is Busy"

Sometimes you'll encounter a more subtle limit. DeepSeek might respond with a "server is busy" message even when their service status shows everything running normally. This tends to happen more often when you're using a large portion of the context window.

![Server is busy message](../images/busy-not-busy.png)

??? info "Screenshot Context"
    This screenshot is not taken by me (LyubomirT) or Omega-Slender. It has been taken from Reddit, and is originally posted by u/Chithrai-Thirunal. If you're the original author, please let me know so I can credit you properly, or remove this note if you prefer not to be credited. Or remove it altogether if you don't want this screenshot here.

The pattern suggests this might be a soft token-based limit, where the system restricts access based on how much computational resource your requests require. Longer conversations with more context seem more likely to trigger this response.

## Working Around Limits

Since IntenseRP Next is essentially a bridge to DeepSeek's web interface, it can't bypass these restrictions. The limits are tied to your DeepSeek account, not to IntenseRP Next itself. But there is a straightforward solution: switch to a different account.

If you hit a limit, you can change to alternative credentials right in the DeepSeek Settings. Just update the email and password fields to your backup account. Keep in mind that if you have persistent cookies enabled, the browser might still be logged into your previous account.

!!! tip "Switching Accounts Cleanly"
    If you have Persistent Cookies enabled, switching accounts might require a few more steps than just changing the credentials. You can either clear the browser data using the **Clear Browser Data** button in Advanced Settings, or manually log out through the DeepSeek interface in the IntenseRP Next browser window. After logging out, it's best to completely restart IntenseRP Next to ensure everything resets properly.

The good news is that these limits seem to be temporary. Accounts that get restricted usually regain access after some time, though the exact duration varies. Having a backup account ready means you can keep your roleplay sessions going without significant interruption.

## Best Practices

To minimize your chances of hitting limits, consider spacing out your requests when possible. If you're running particularly long sessions with extensive context, you might want to start fresh conversations periodically rather than maintaining extremely long threads.

Remember that these restrictions come from DeepSeek's side, and they might change their policies at any time. What works today might be different tomorrow, so staying flexible with backup options is your best strategy.