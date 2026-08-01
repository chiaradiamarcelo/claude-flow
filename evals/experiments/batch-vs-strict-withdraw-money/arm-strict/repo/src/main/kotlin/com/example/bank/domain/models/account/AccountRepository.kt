package com.example.bank.domain.models.account

interface AccountRepository {

    fun save(account: Account)

    fun findById(accountId: String): Account?
}
