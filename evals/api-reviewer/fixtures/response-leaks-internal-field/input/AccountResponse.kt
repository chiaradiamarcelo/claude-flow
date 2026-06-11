package banking.api.dto

data class AccountResponse(
    val accountId: String,
    val balanceCents: Long,
    val internalDbRowId: Long,
    val passwordHash: String,
    val ledgerShardKey: String,
)
