package com.example.bank.domain.query

interface AccountOverviewQuery {

    fun findByAccountId(accountId: String): AccountOverviewView?
}
