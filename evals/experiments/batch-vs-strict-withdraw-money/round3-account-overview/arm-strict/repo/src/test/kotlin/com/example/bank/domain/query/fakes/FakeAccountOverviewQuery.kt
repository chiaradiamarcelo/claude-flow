package com.example.bank.domain.query.fakes

import com.example.bank.domain.query.AccountOverviewQuery
import com.example.bank.domain.query.AccountOverviewView

class FakeAccountOverviewQuery : AccountOverviewQuery {

    private val overviews = mutableListOf<AccountOverviewView>()

    fun seed(overview: AccountOverviewView) {
        overviews.add(overview)
    }

    override fun findByAccountId(accountId: String): AccountOverviewView? =
        overviews.find { it.accountId == accountId }
}
