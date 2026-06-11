package banking.domain.models.account

import banking.api.dto.OpenAccountRequest

class Account private constructor(
    val id: String,
    private var balanceCents: Long,
) {
    fun balance(): Long = balanceCents

    fun deposit(amountCents: Long) {
        balanceCents += amountCents
    }

    companion object {
        fun openFrom(request: OpenAccountRequest): Account =
            Account(request.ownerId, request.initialBalanceCents)
    }
}
