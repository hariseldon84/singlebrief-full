# Foreign Key Cascade Policy

## Policy Rules

### CASCADE (Delete child when parent is deleted)
- **Users → Sessions, Consents, Memories, Preferences**: When user is deleted, remove all personal data
- **Organizations → Teams, Users, Privacy Settings**: When org is deleted, remove all org data
- **Teams → Team Memories, Team Settings**: When team is deleted, remove team-specific data
- **Conversations → Messages**: When conversation is deleted, remove all messages
- **Integrations → Logs, Health Checks**: When integration is deleted, remove related data

### SET NULL (Preserve child, nullify reference)
- **Users → Audit Logs**: Preserve audit trail even when user is deleted
- **Teams → Optional References**: When team is deleted, preserve records but clear team reference
- **Organizations → Audit Logs**: Preserve audit trail when org is deleted

### RESTRICT (Prevent deletion if children exist)
- **Organizations → Active Users**: Prevent org deletion if active users exist
- **Templates → Active Briefs**: Prevent template deletion if briefs use it

## Implementation Status
✅ Implemented consistent CASCADE policies across all models