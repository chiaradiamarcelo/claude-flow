package com.example.bank.api

import com.example.bank.api.dto.AccountOverviewResponse
import com.example.bank.domain.query.AccountOverviewQuery
import com.example.bank.domain.query.AccountOverviewView
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RestController

@RestController
class AccountOverviewController(
    private val accountOverviews: AccountOverviewQuery,
) {

    @GetMapping("/accounts/{accountId}/overview")
    fun overview(@PathVariable accountId: String): AccountOverviewResponse {
        val overview = accountOverviews.findByAccountId(accountId)
            ?: throw AccountNotFoundException(accountId)

        return toResponse(overview)
    }

    private fun toResponse(overview: AccountOverviewView): AccountOverviewResponse =
        AccountOverviewResponse(overview.accountId, overview.balance, overview.tier)
}
