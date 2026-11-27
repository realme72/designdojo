# WhatsApp channel

Add a fourth channel, `WHATSAPP` (it comes last in channel order).

- WhatsApp only allows **pre-approved templates**: new `approve_template(template_id)`
  (unknown → `UnknownTemplate`). A send of an unapproved template on WhatsApp gets the new
  status `SKIPPED` (not sent, doesn't count toward rate limits). Other channels don't care.
- Everything else (preferences, rate limits, provider outages, outbox) works for WhatsApp
  exactly as for the other channels.

*Interviewer's question:* where did the approval rule end up, and did send() change?
