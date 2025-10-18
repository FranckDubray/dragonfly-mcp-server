def build_execution_graph():
    mermaid = """
flowchart TD
  START(START) --> has_more_mailboxes{more mailboxes ?}
  has_more_mailboxes -->|oui| imap_search_unseen_oldest(imap search unseen oldest)
  has_more_mailboxes -->|non| sleep_interval(sleep interval)
  sleep_interval --> START

  imap_search_unseen_oldest --> has_unseen{has unseen ?}
  has_unseen -->|oui| imap_get_message_full(imap get message full)
  has_unseen -->|non| has_more_mailboxes

  imap_get_message_full --> body_over_30kb{body over 30kb ?}
  body_over_30kb -->|oui| prepare_truncated_view(prepare truncated view)
  body_over_30kb -->|non| use_full_body(use full body)
  prepare_truncated_view --> sanitize_text(sanitize text)
  use_full_body --> sanitize_text
  sanitize_text --> call_llm_classify_both(call llm classify both)

  %% LLM fallback loop: retry after 60s on error
  call_llm_classify_both -.-|retry 60s| call_llm_classify_both

  call_llm_classify_both --> class_branch{spam ham}
  class_branch -->|spam| log_spam_db(log spam db)
  class_branch -->|ham| log_ham_db(log ham db)

  log_spam_db --> imap_move_to_spam(imap move to spam)
  imap_move_to_spam --> imap_search_unseen_oldest

  log_ham_db --> imap_mark_read(imap mark read)
  imap_mark_read --> imap_search_unseen_oldest
"""
    return {"mermaid": mermaid.strip()}
