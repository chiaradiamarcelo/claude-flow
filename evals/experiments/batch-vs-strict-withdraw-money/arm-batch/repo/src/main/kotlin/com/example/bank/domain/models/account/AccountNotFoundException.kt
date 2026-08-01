package com.example.bank.domain.models.account

class AccountNotFoundException(accountId: String) :
    RuntimeException("No account exists with id $accountId")
