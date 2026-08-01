package com.example.bank.api

import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.bind.annotation.RestControllerAdvice

@RestControllerAdvice
class ApiExceptionHandler {

    @ExceptionHandler(AccountNotFoundException::class)
    fun handleAccountNotFound(exception: AccountNotFoundException): ResponseEntity<Unit> =
        ResponseEntity.status(HttpStatus.NOT_FOUND).build()
}
