package com.example.bank.domain.models.account

import java.math.BigDecimal

class Account(
    val accountId: String,
    val balance: BigDecimal,
) {

    fun deposit(amount: BigDecimal): Account {
        if (isNotPositive(amount)) throw InvalidDepositAmountException(amount)

        return Account(accountId, balance + amount)
    }

    private fun isNotPositive(amount: BigDecimal): Boolean = amount <= BigDecimal.ZERO

    override fun equals(other: Any?): Boolean = other is Account && other.accountId == accountId

    override fun hashCode(): Int = accountId.hashCode()
}
