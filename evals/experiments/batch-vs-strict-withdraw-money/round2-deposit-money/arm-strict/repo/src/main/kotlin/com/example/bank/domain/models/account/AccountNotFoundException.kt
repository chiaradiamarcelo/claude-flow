package com.example.bank.domain.models.account

class AccountNotFoundException(accountId: String) :
    RuntimeException("Account $accountId was not found")
