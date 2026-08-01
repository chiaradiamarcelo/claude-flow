package com.example.bank.domain.models.account

import java.math.BigDecimal

/**
 * Account aggregate root. Identity is [accountId]; equality is identity-only.
 * Owns the withdrawal invariants (strictly positive amount, no overdraft).
 */
class Account(
    private val accountId: String,
    private val balance: BigDecimal,
) {

    fun accountId(): String = accountId

    fun balance(): BigDecimal = balance

    fun withdraw(amount: BigDecimal): Account {
        if (isNotPositive(amount)) throw InvalidWithdrawalAmountException(amount)
        if (exceedsBalance(amount)) throw InsufficientFundsException(accountId, amount, balance)

        return Account(accountId, balance.subtract(amount))
    }

    private fun isNotPositive(amount: BigDecimal): Boolean = amount <= BigDecimal.ZERO

    private fun exceedsBalance(amount: BigDecimal): Boolean = amount > balance

    override fun equals(other: Any?): Boolean =
        this === other || (other is Account && accountId == other.accountId)

    override fun hashCode(): Int = accountId.hashCode()

    override fun toString(): String = "Account(accountId=$accountId, balance=$balance)"
}
