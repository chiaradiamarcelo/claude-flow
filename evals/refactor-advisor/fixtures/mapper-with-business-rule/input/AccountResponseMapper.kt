package banking.api

import banking.api.dto.AccountResponse
import banking.domain.models.account.Account

class AccountResponseMapper {

    fun toResponse(account: Account): AccountResponse {
        val tier = when {
            account.balance() >= 1_000_000 -> "GOLD"
            account.balance() >= 100_000 -> "SILVER"
            else -> "BRONZE"
        }
        val overdraftAllowed = account.balance() >= 50_000
        return AccountResponse(
            accountId = account.id,
            balanceCents = account.balance(),
            tier = tier,
            overdraftAllowed = overdraftAllowed,
        )
    }
}
