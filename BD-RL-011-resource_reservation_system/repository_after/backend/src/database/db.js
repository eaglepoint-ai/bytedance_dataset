const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');

const DB_PATH = process.env.DATABASE_PATH || './database.sqlite';
const SCHEMA_PATH = path.join(__dirname, 'schema.sql');

class Database {
  constructor() {
    this.db = null;
  }

  initialize() {
    return new Promise((resolve, reject) => {
      this.db = new sqlite3.Database(DB_PATH, (err) => {
        if (err) {
          return reject(err);
        }

        const schema = fs.readFileSync(SCHEMA_PATH, 'utf8');
        
        this.db.exec(schema, (execErr) => {
          if (execErr) {
            return reject(execErr);
          }
          resolve();
        });
      });
    });
  }

  run(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.run(sql, params, function(err) {
        if (err) {
          return reject(err);
        }
        resolve({ lastID: this.lastID, changes: this.changes });
      });
    });
  }

  get(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.get(sql, params, (err, row) => {
        if (err) {
          return reject(err);
        }
        resolve(row);
      });
    });
  }

  all(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.all(sql, params, (err, rows) => {
        if (err) {
          return reject(err);
        }
        resolve(rows);
      });
    });
  }

  beginTransaction() {
    return this.run('BEGIN IMMEDIATE TRANSACTION');
  }

  commit() {
    return this.run('COMMIT');
  }

  rollback() {
    return this.run('ROLLBACK');
  }

  close() {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        return resolve();
      }
      
      this.db.close((err) => {
        if (err) {
          return reject(err);
        }
        resolve();
      });
    });
  }
}

const database = new Database();

module.exports = database;
