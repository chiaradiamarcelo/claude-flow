package com.example.bank.domain.models.account

import java.math.BigDecimal

class BankAccount(
    val id: String,
    balance: BigDecimal,
) {
    var balance: BigDecimal = balance
        private set

    fun withdraw(amount: BigDecimal) {
        if (amount <= BigDecimal.ZERO) throw IllegalArgumentException("amount must be positive")
        if (amount > balance) throw IllegalStateException("insufficient funds")
        balance = balance - amount
    }

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is BankAccount) return false
        return id == other.id
    }

    override fun hashCode(): Int = id.hashCode()
}
