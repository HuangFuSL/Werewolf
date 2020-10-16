# Werewolf

The final project of Computer Network in 2020A, written in Python.

## Weekly Report Summary

* 2020/10/12
  * **IMPORTANT** Prerequisite: Implement a application layer protocol.  
    * Possible reference `urllib` or `requests`
    * The program sends and receives chuncked data rather than the plain text (raw data).
  * Function Demand: Implement the werewolf game rule (at most 12 players)
  * Tasks
    * Collect the game rule and demo applications;
    * Collect demo implementations.
 * 2020/10/16
  * Implementation framework
    * Protocol
    * Player's identity
    * Server
    * Client
    * GUI
  * 

### From 2020/10/12

Function Demand: Gamerule

* TODO: List the gamerule here.

Demo implementation:

* [https://github.com/GeminiLab/OOPLRS](https://github.com/GeminiLab/OOPLRS) (C++ & Qt)
* [https://github.com/Terund/Werewolf](https://github.com/Terund/Werewolf) (Python, not fully implemented)

Protocol implementation: Please refer to its [introduction](Werewolf/WP/README.md) page

### From 2020/10/16

Function Demand: Player's identity

所有的人抽象成基类，所需的属性与方法如下：

1. 编号属性
2. 投票、上警和发言方法
3. 警长属性
4. 是否好人属性

村民属于子类，神和狼属于另一个子类

村民子类不需要额外的功能

神和狼作为一个类， 1定义一个虚函数表示他们可以执行的操作，加一个执行条件

具体实现：
