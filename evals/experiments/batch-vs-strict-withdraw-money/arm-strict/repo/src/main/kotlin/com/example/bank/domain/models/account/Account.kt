package com.example.bank.domain.models.account

import java.math.BigDecimal

class Account(
    private val accountId: String,
    private val balance: BigDecimal,
) {

    fun accountId(): String = accountId

    fun balance(): BigDecimal = balance

    fun withdraw(amount: BigDecimal): Account {
        if (isNotPositive(amount)) throw InvalidWithdrawalAmountException(amount)
        if (exceedsBalance(amount)) throw InsufficientFundsException(accountId, amount)

        return Account(accountId, balance - amount)
    }

    override fun equals(other: Any?): Boolean = other is Account && other.accountId == accountId

    override fun hashCode(): Int = accountId.hashCode()

    private fun isNotPositive(amount: BigDecimal): Boolean = amount.signum() <= 0

    private fun exceedsBalance(amount: BigDecimal): Boolean = amount > balance
}
