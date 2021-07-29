db
use test
db.createUser(
    {
        user: "myTester",
        pwd: "xyz123",
        roles: [ { role: "readWrite", db: "test" },
            { role: "read", db: "reporting" } ]
    }
)
db.foo.insert( { x: 1, y: 1 } )
show dbs
show collections
db.getCollectionNames();
db.printCollectionStats()
show users
show roles
show profile
show databases
use myNewDatabase
db.hostInfo()
db.myCollection.insertOne( { x: 1 } );
db.getCollection("3 test").find()
db.getCollection("3-test").find()
db.getCollection("stats").find()
db.inventory.insertMany([
    // MongoDB adds the _id field with an ObjectId if _id is not present
    { item: "journal", qty: 25, status: "A",
        size: { h: 14, w: 21, uom: "cm" }, tags: [ "blank", "red" ] },
    { item: "notebook", qty: 50, status: "A",
        size: { h: 8.5, w: 11, uom: "in" }, tags: [ "red", "blank" ] },
    { item: "paper", qty: 100, status: "D",
        size: { h: 8.5, w: 11, uom: "in" }, tags: [ "red", "blank", "plain" ] },
    { item: "planner", qty: 75, status: "D",
        size: { h: 22.85, w: 30, uom: "cm" }, tags: [ "blank", "red" ] },
    { item: "postcard", qty: 45, status: "A",
        size: { h: 10, w: 15.25, uom: "cm" }, tags: [ "blue" ] }
]);
db.inventory.find( {} )
db.inventory.find( { status: "D" } )
db.inventory.find( { size: { h: 14, w: 21, uom: "cm" } } )
db.inventory.find( { "size.uom": "in" } )
db.inventory.find( { tags: "red" } )
db.inventory.find( { tags: ["red", "blank"] } )
use myNewDB
db.myNewCollection1.insertOne( { x: 1 } )
db.myNewCollection2.insertOne( { x: 1 } )
db.myNewCollection3.createIndex( { y: 1 } )
db.runCommand( { create: <view>, viewOn: <source>, pipeline: <pipeline> } )
db.runCommand( { create: <view>, viewOn: <source>, pipeline: <pipeline>, collation: <collation> } )
db.createView(<view>, <source>, <pipeline>, <collation> )
db.view.find().sort({$natural: 1})
db.createCollection( "log", { capped: true, size: 100000 } )
db.createCollection("log", { capped : true, size : 5242880, max : 5000 } )
db.cappedCollection.find().sort( { $natural: -1 } )
db.collection.isCapped()
db.runCommand({"convertToCapped": "mycoll", size: 100000});
var mydoc = {
    _id: ObjectId("5099803df3f4948bd2f98391"),
    name: { first: "Alan", last: "Turing" },
    birth: new Date('Jun 23, 1912'),
    death: new Date('Jun 07, 1954'),
    contribs: [ "Turing machine", "Turing test", "Turingery" ],
    views : NumberLong(1250000)
}
var a = new Timestamp();
db.test.insertOne( { ts: a } );
{ "_id" : ObjectId("542c2b97bac0595474108b48"), "ts" : Timestamp(1412180887, 1) }
var mydate1 = new Date()
var mydate2 = ISODate()
mydate1.toString()
mydate1.getMonth()
{
    locale: <string>,
    caseLevel: <boolean>,
    caseFirst: <string>,
    strength: <int>,
    numericOrdering: <boolean>,
    alternate: <string>,
    maxVariable: <string>,
    backwards: <boolean>
}
{ "$binary": "<bindata>", "$type": "<t>" }
db.json.insert( { longQuoted : NumberLong("9223372036854775807") } )
db.json.insert( { longUnQuoted : NumberLong(9223372036854775807) } )
db.json.find()
db.json.insert( { decimalQuoted : NumberDecimal("123.40") } )
db.json.insert( { decimalUnQuoted : NumberDecimal(123.40) } )
db.json.find()
db.students.drop( { writeConcern: { w: "majority" } } )
db.students.drop()
db.printCollectionStats()
db.printReplicationInfo()
db.printShardingStatus()
db.printSlaveReplicationInfo()
db.repairDatabase()
db.resetError()
db.getMongo()
exit