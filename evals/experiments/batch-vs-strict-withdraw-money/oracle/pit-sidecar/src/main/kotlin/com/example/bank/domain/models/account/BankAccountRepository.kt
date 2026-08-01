package com.example.bank.domain.models.account

interface BankAccountRepository {
    fun findById(id: String): BankAccount
    fun save(account: BankAccount)
}
